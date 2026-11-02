import os
import logging
import numpy as np
from pathlib import Path
from typing import List, Optional

from src.config import PROCESSED_DATA_DIR

logger = logging.getLogger("ml.embeddings")

class EmbeddingGenerator:
    """
    Generates dense vector embeddings for feedback texts and extracted insights.
    Implements local disk caching and multi-tier fallbacks:
      1. sentence-transformers (all-MiniLM-L6-v2) if installed
      2. Google GenAI text-embedding-004 if GEMINI_API_KEY configured
      3. Scikit-learn TF-IDF + TruncatedSVD dense 64-dimensional semantic vectors (zero-dependency, offline)
    """

    def __init__(self, cache_file: Optional[str] = None):
        self.cache_path = Path(cache_file) if cache_file else PROCESSED_DATA_DIR / "embeddings_cache.npz"
        self.backend = None
        self._init_backend()

    def _init_backend(self):
        # 1. Check sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.backend = "sentence_transformers"
            logger.info("Initialized sentence-transformers (all-MiniLM-L6-v2) for embeddings.")
            return
        except Exception:
            pass

        # 2. Check GenAI
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=api_key)
                self.backend = "genai"
                logger.info("Initialized Google GenAI embeddings (text-embedding-004).")
                return
            except Exception:
                pass

        # 3. Fallback to Scikit-Learn TF-IDF + TruncatedSVD
        self.backend = "sklearn_lsa"
        logger.info("Initialized Scikit-Learn TF-IDF + TruncatedSVD dense semantic embeddings engine.")

    def generate(self, texts: List[str], use_cache: bool = True) -> np.ndarray:
        """
        Generates dense normalized embeddings of shape (N, D).
        """
        if not texts:
            return np.empty((0, 64), dtype=np.float32)

        # 1. Try cache if available and lengths match
        if use_cache and self.cache_path.exists():
            try:
                data = np.load(self.cache_path, allow_pickle=True)
                cached_embeddings = data["embeddings"]
                cached_texts = data["texts"]
                if len(cached_texts) == len(texts) and all(t1 == t2 for t1, t2 in zip(cached_texts, texts)):
                    logger.info(f"Loaded {len(texts)} embeddings from cache: {self.cache_path}")
                    return cached_embeddings
            except Exception as e:
                logger.warning(f"Could not read embedding cache: {e}")

        logger.info(f"Computing embeddings for {len(texts)} items via backend: '{self.backend}'...")

        if self.backend == "sentence_transformers":
            embeddings = self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            embeddings = np.array(embeddings, dtype=np.float32)

        elif self.backend == "genai":
            try:
                vectors = []
                for t in texts:
                    res = self.genai_client.models.embed_content(
                        model="text-embedding-004",
                        contents=t,
                    )
                    vectors.append(res.embedding.values)
                embeddings = np.array(vectors, dtype=np.float32)
                # L2 normalize
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / np.maximum(norms, 1e-12)
            except Exception as e:
                logger.warning(f"GenAI batch embed failed: {e}. Falling back to Sklearn LSA.")
                embeddings = self._generate_sklearn_lsa(texts)

        else:
            embeddings = self._generate_sklearn_lsa(texts)

        # Save to disk cache
        try:
            np.savez_compressed(self.cache_path, embeddings=embeddings, texts=texts)
            logger.info(f"Saved {len(texts)} embeddings to cache at {self.cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save embeddings cache: {e}")

        return embeddings

    def _generate_sklearn_lsa(self, texts: List[str]) -> np.ndarray:
        """
        Constructs dense semantic LSA representations using TF-IDF + TruncatedSVD.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        vectorizer = TfidfVectorizer(
            max_features=2500,
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
            min_df=1
        )
        from sklearn.preprocessing import normalize
        tfidf = vectorizer.fit_transform(texts)

        n_samples = tfidf.shape[0]
        n_features = tfidf.shape[1]

        if n_samples < 20 or n_features < 20:
            return normalize(tfidf.toarray(), norm="l2").astype(np.float32)

        n_components = min(48, n_samples - 1, n_features - 1)
        if n_components < 2:
            return normalize(tfidf.toarray(), norm="l2").astype(np.float32)

        svd = TruncatedSVD(n_components=n_components, random_state=42)
        dense = svd.fit_transform(tfidf)
        return normalize(dense, norm="l2").astype(np.float32)
