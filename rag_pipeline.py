import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma

class OperationalRAGPipeline:
    def __init__(self, file_path: str = "data/operational_policies.txt", persist_directory: str = "vector_db"):
        self.file_path = file_path
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Chunking and Embeddings setup for operational knowledge base."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Operational manual not found: {self.file_path}")
            
        loader = TextLoader(self.file_path, encoding="utf-8")
        documents = loader.load()

        # Chunking strategy for detailed operational manual
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)
        chunks = text_splitter.split_documents(documents)

        # Vector Store Creation
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )

    def hybrid_search(self, query: str, top_k: int = 3) -> list[str]:
        """Hybrid/Similarity search to retrieve relevant operational rules."""
        results = self.vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]

    def self_rag_verification(self, query: str, retrieved_docs: list[str]) -> bool:
        """Self-RAG Verification: Validates context relevance to prevent hallucinations."""
        if not retrieved_docs:
            return False
            
        llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        context = "\n".join(retrieved_docs)
        prompt = (
            f"Given the operational query: '{query}', is the following retrieved manual context relevant and sufficient to formulate an answer?\n"
            f"Context: {context}\n"
            f"Respond ONLY with YES or NO."
        )
        
        response = llm.invoke(prompt).content.strip().upper()
        return "YES" in response