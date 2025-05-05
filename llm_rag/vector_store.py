import chromadb
from chromadb.utils import embedding_functions

from .config import DB_PATH, CHUNK_SIZE
from .utils import get_chunk_text


class ChromaVectorStore:
    def __init__(self):
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        self.client = chromadb.PersistentClient(DB_PATH)
        self.store = self.client.get_or_create_collection(
            name="documents",
            embedding_function=self.embedder
        )

    def upload_document(self, text, metadata=None):
        document_chunks = get_chunk_text(text, CHUNK_SIZE)
        chucks_count = len(self.store.get()["ids"]) if self.store.count() > 0 else 0
        ids = [f'chunk_{chucks_count + i}' for i in range(len(document_chunks))]
        metadatas = [metadata or {} for _ in document_chunks]

        self.store.add(
            documents=document_chunks,
            metadatas=metadatas,
            ids=ids
        )

        return len(document_chunks)

    def get_chunks_by_query(self, query, top_k=5):
        text_vectors = self.store.query(query_texts=[query], n_results=top_k)

        return [
            {
                "text": document, "metadata": metadata, "distance": distance
            }
            for document, metadata, distance in zip(
                text_vectors['documents'][0], text_vectors['metadatas'][0], text_vectors['distances'][0]
            )
        ]
