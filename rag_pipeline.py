import os
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma

load_dotenv()

# Anchor paths relative to this file's location (Project Root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "operational_policies.txt")
DEFAULT_VECTOR_DB_PATH = os.path.join(PROJECT_ROOT, "vector_db")


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
        self.llm = None
        
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Chunking and Embeddings setup for operational knowledge base."""
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )
            return

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Operational manual not found: {self.file_path}")

        loader = TextLoader(self.file_path, encoding="utf-8")
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)
        chunks = text_splitter.split_documents(documents)

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
                model="gemini-3.6-flash",
                google_api_key=api_key,
                temperature=0,
            )
        return self.llm

    def hybrid_search(self, query: str, top_k: int = 3) -> list[str]:
        """Similarity search to retrieve relevant operational rules."""
        results = self.vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]

    def self_rag_verification(self, query: str, retrieved_docs: list[str]) -> bool:
        """Self-RAG Verification using Gemini Chat."""
        if not retrieved_docs:
            return False

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