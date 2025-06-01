from openai import OpenAI
from pgvector import Vector
from src.logger import get_module_logger

logger = get_module_logger(__name__)

class Embedder:
    def __init__(self):
        # Point to your local embeddings server
        self.client = OpenAI(
            api_key="EMPTY",  # The server doesn't require a real API key
            base_url="http://lab.internal:8008/v1"
        )
        logger.info("Embedder initialized with HuggingFace text embeddings server")

    def embed(self, text: str) -> Vector:
        """
        Generate embeddings for the given text using the HuggingFace text embeddings server.
        
        Args:
            text (str): The input text to embed
            
        Returns:
            Vector: The embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model="sentence-transformers/all-MiniLM-L6-v2",
                input=text
            )
            return Vector(response.data[0].embedding)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise