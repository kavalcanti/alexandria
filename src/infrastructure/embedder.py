import os
from sentence_transformers import SentenceTransformer
from pgvector import Vector

class Embedder:
    def __init__(self):
        self.model_name: str = os.getenv("EMBD_MODEL")
        self.local_embeddings_dir: str = f"ai_models/{self.model_name}"
        self.embeddings_download_cache_dir: str = f"ai_models/cache"
        
        self.model = self._load_local_embeddings()

        return None

    def _load_local_embeddings(self) -> SentenceTransformer:
        """
        Loads or downloads the sentence transformers embeddings model.
        
        This method checks if the model exists in the local directory. If not, it downloads
        the model from HuggingFace, saves it locally, and then reloads it from the local
        directory to ensure consistent loading behavior.
        
        Returns:
            tuple: (AutoTokenizer, AutoModelForCausalLM) The loaded tokenizer and model instances
        """

        if not os.path.exists(self.local_embeddings_dir):
            
            embeddings_model = SentenceTransformer(self.model_name)
            os.makedirs(self.local_embeddings_dir)
            embeddings_model.save_pretrained(self.local_embeddings_dir)

            embeddings_model = None

        embeddings_model = SentenceTransformer(self.local_embeddings_dir)

        return embeddings_model

    def embed(self, text: str) -> Vector:
        return self.model.encode(text)