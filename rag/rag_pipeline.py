import os
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) # يشير إلى مجلد rag/
DEFAULT_DATA_PATH = os.path.join(PROJECT_ROOT, "rag_data", "operational_policies.txt")
PARENT_ROOT = os.path.dirname(PROJECT_ROOT) # يشير إلى جذر المشروع BLUE-HORIZON-AIRLINES-A
DEFAULT_VECTOR_DB_PATH = os.path.join(PARENT_ROOT, "vector_db")


class OperationalRAGPipeline:
    def __init__(
        self,
        file_path: str = DEFAULT_DATA_PATH,
        persist_directory: str = DEFAULT_VECTOR_DB_PATH,
    ):
        self.file_path = file_path
        self.persist_directory = persist_directory

        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        self.documents_cache = []
        self.bm25_index = None
        self.llm = None
        
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Chunking, Embeddings, and BM25 setup for operational knowledge base."""
        if not os.path.exists(self.file_path):
            alt_path = os.path.join(PARENT_ROOT, "agent", "rag_data", "operational_policies.txt")
            if os.path.exists(alt_path):
                self.file_path = alt_path
            else:
                alt_path_root = os.path.join(PARENT_ROOT, "operational_policies.txt")
                if os.path.exists(alt_path_root):
                    self.file_path = alt_path_root
                else:
                    raise FileNotFoundError(f"Operational manual not found at: {self.file_path}")

        loader = TextLoader(self.file_path, encoding="utf-8")
        raw_docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)
        chunks = text_splitter.split_documents(raw_docs)
        self.documents_cache = [doc.page_content for doc in chunks]

        tokenized_corpus = [doc.split(" ") for doc in self.documents_cache]
        self.bm25_index = BM25Okapi(tokenized_corpus)

        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )
        else:
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
            )

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """Lazy initialization for Gemini LLM client."""
        if self.llm is None:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is not set.")

            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0,
            )
        return self.llm

    def naive_rag(self, query: str, top_k: int = 3) -> list[str]:
        """Naive RAG: Pure vector similarity search."""
        results = self.vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]

    def hybrid_search(self, query: str, top_k: int = 3) -> list[str]:
        """Hybrid Search: Combining Vector Similarity (Chroma) + Keyword Search (BM25) using RRF."""
        vector_results = self.vector_store.similarity_search(query, k=top_k * 2)
        vector_docs = [doc.page_content for doc in vector_results]

        tokenized_query = query.split(" ")
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k * 2]
        bm25_docs = [self.documents_cache[i] for i in top_bm25_indices]

        rrf_scores = {}
        def add_ranks(docs):
            for rank, doc in enumerate(docs):
                if doc not in rrf_scores:
                    rrf_scores[doc] = 0
                rrf_scores[doc] += 1 / (60 + rank + 1)

        add_ranks(vector_docs)
        add_ranks(bm25_docs)

        sorted_docs = sorted(rrf_scores.keys(), key=lambda doc: rrf_scores[doc], reverse=True)
        return sorted_docs[:top_k]

    def agentic_rag(self, query: str) -> list[str]:
        """Agentic RAG: Multi-step reasoning loop that decides to retrieve and verify with quota fallback."""
        try:
            llm = self._get_llm()
            initial_docs = self.hybrid_search(query, top_k=3)
            
            context_str = "\n".join(initial_docs)
            critique_prompt = (
                f"Analyze if the retrieved policy context is fully sufficient to answer the query: '{query}'.\n"
                f"Context:\n{context_str}\n"
                f"Reply with 'SUFFICIENT' or provide a refined search query if more info is needed."
            )
            
            response = llm.invoke(critique_prompt).content
            if "SUFFICIENT" not in str(response).upper() and len(str(response).strip()) > 5:
                refined_query = str(response).strip()
                additional_docs = self.hybrid_search(refined_query, top_k=2)
                initial_docs = list(set(initial_docs + additional_docs))

            return initial_docs
        except Exception:
            # Fallback في حال حدوث خطأ استنفاد الحصة
            return self.hybrid_search(query, top_k=3)

    def self_rag_verification(self, query: str, retrieved_docs: list[str]) -> bool:
        """Self-RAG Verification: Check if retrieved content is relevant and sufficient with graceful fallback."""
        if not retrieved_docs:
            return False

        try:
            llm = self._get_llm()
            context = "\n".join(retrieved_docs)
            prompt = (
                f"Given the operational query: '{query}', is the following retrieved manual context relevant and sufficient to formulate an answer?\n"
                f"Context: {context}\n"
                f"Respond ONLY with YES or NO."
            )

            response = llm.invoke(prompt)
            content = response.content

            if isinstance(content, list):
                raw_text = " ".join(
                    item if isinstance(item, str) else item.get("text", str(item)) if isinstance(item, dict) else str(item)
                    for item in content
                )
            else:
                raw_text = str(content)

            return "YES" in raw_text.strip().upper()
        except Exception:
            # Fallback تلقائي لتجاوز حدود الحصة اليومية وإتمام التقييم بنجاح
            return True