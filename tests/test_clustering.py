import pytest
import numpy as np
from src.ml.embeddings import EmbeddingGenerator
from src.ml.clustering import SemanticClusterer
from src.ml.theme_namer import ThemeNamer
from src.ml.theme_review import ThemeReviewManager
from src.db.database import get_db, init_db
from src.db.models import Theme, ItemThemeMapping

def test_embedding_generation():
    embedder = EmbeddingGenerator()
    texts = [
        "Bank mandate bounce fee on Groww SIP debit date.",
        "Negative XIRR return in month 3 mutual fund.",
        "NAV cut off settlement takes 2 business days."
    ]
    vectors = embedder.generate(texts, use_cache=False)
    assert isinstance(vectors, np.ndarray)
    assert vectors.shape[0] == 3
    assert vectors.shape[1] > 0
    # Verify L2 normalization
    norms = np.linalg.norm(vectors, axis=1)
    for norm in norms:
        assert abs(norm - 1.0) < 1e-3

def test_semantic_clustering():
    clusterer = SemanticClusterer(min_clusters=2, max_clusters=4)
    # Generate 10 synthetic samples with 2 separated clusters
    vecs_a = np.random.normal(loc=1.0, scale=0.1, size=(5, 16))
    vecs_b = np.random.normal(loc=-1.0, scale=0.1, size=(5, 16))
    embeddings = np.vstack([vecs_a, vecs_b])
    # Normalize
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    items = [{"id": f"item_{i}", "raw_text": f"Sample text {i}", "severity": 2} for i in range(10)]
    res = clusterer.cluster(embeddings, items)

    assert "clusters" in res
    assert res["total_clusters"] >= 2
    for cid, cdata in res["clusters"].items():
        assert "items" in cdata
        assert "exemplars" in cdata
        assert len(cdata["exemplars"]) <= 2

def test_theme_namer():
    namer = ThemeNamer()
    cluster_sample = {
        "items": [
            {
                "id": "1",
                "raw_text": "Salary date is 7th and mandate bounce fee 590 was charged by bank. Cancelled SIP.",
                "drop_trigger": "payment_failure",
                "severity": 5,
                "journey_stage": "month_1_3"
            },
            {
                "id": "2",
                "raw_text": "Autopay bounce charge 590 rs because salary came late on Groww.",
                "drop_trigger": "payment_failure",
                "severity": 5,
                "journey_stage": "month_1_3"
            }
        ],
        "exemplars": [
            {"raw_text": "Salary date is 7th and mandate bounce fee 590 was charged by bank."}
        ]
    }
    named = namer.name_cluster(cluster_sample)
    assert "Salary" in named["title"] or "Bounce" in named["title"] or "Autopay" in named["title"]
    assert named["taxonomy_type"] in ["inductive", "deductive"]
    assert named["avg_severity"] == 5.0

