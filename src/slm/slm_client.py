
import os
from typing import List
import google.generativeai as genai

class SLMClient:
    """Client for interacting with smaller models, like embedding models."""
    def __init__(self, api_key: str = None, model: str = "models/embedding-001"):
        """
        Initializes the SLMClient.

        Args:
            api_key (str): The Google API key. If not provided, it will
                           look for the GOOGLE_API_KEY environment variable.
            model (str): The name of the embedding model to use.
        """
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not provided or found in GOOGLE_API_KEY environment variable.")
        
        genai.configure(api_key=api_key)
        self.model = model

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of texts.

        Args:
            texts (List[str]): A list of strings to embed.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """
        if not texts:
            return []
        try:
            result = genai.embed_content(
                model=self.model,
                content=texts,
                task_type="RETRIEVAL_DOCUMENT"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            return [[] for _ in texts]
