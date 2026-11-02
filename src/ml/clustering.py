import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from sklearn.metrics import silhouette_score
from sklearn.cluster import AgglomerativeClustering, KMeans

logger = logging.getLogger("ml.clustering")

class SemanticClusterer:
    """
    Performs unsupervised semantic clustering over dense feedback embeddings.
    Isolates natural thematic clusters (targeting 8-15 distinct behavioral problem areas)
    and labels outliers.
    """

    def __init__(self, min_clusters: int = 6, max_clusters: int = 14):
        self.min_clusters = min_clusters
        self.max_clusters = max_clusters

    def cluster(
        self,
        embeddings: np.ndarray,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes clustering and returns grouped items with distance metrics.
        """
        n_samples = len(items)
        if n_samples == 0:
            return {"clusters": {}, "outliers": []}

        if n_samples < self.min_clusters:
            # Not enough items to cluster into distinct themes
            clusters = {
                0: {
                    "cluster_id": 0,
                    "items": items,
                    "exemplars": items[:2],
                    "centroid": np.mean(embeddings, axis=0) if len(embeddings) > 0 else None,
                }
            }
            return {"clusters": clusters, "outliers": []}

        # 1. Attempt HDBSCAN if installed
        try:
            import hdbscan
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=max(3, n_samples // 15),
                min_samples=2,
                metric="euclidean"
            )
            labels = clusterer.fit_predict(embeddings)
            unique_labels = set(labels)
            # If HDBSCAN found a meaningful number of clusters (>3)
            if len([l for l in unique_labels if l != -1]) >= 4:
                logger.info(f"HDBSCAN discovered {len(unique_labels) - (1 if -1 in unique_labels else 0)} clusters.")
                return self._package_clusters(labels, embeddings, items)
        except Exception:
            pass

        # 2. Optimized Silhouette-guided Agglomerative / KMeans Clustering
        max_k = min(self.max_clusters, n_samples - 1)
        min_k = min(self.min_clusters, max_k)
        
        best_k = min_k
        best_score = -1.0

        for k in range(min_k, max_k + 1):
            try:
                cluster_model = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
                lbls = cluster_model.fit_predict(embeddings)
                score = silhouette_score(embeddings, lbls, metric="cosine")
                if score > best_score:
                    best_score = score
                    best_k = k
            except Exception:
                continue

        logger.info(f"Optimal cluster count determined: k={best_k} (Silhouette Score: {best_score:.3f})")
        final_model = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = final_model.fit_predict(embeddings)

        return self._package_clusters(labels, embeddings, items)

    def _package_clusters(
        self,
        labels: np.ndarray,
        embeddings: np.ndarray,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates cluster centroids, distances, and selects 2 exemplar quotes closest to centroid.
        """
        cluster_groups = defaultdict(list)
        cluster_vectors = defaultdict(list)

        for idx, (label, item) in enumerate(zip(labels, items)):
            cluster_groups[label].append(item)
            cluster_vectors[label].append(embeddings[idx])

        clusters_result = {}
        outliers = []

        for label, group_items in cluster_groups.items():
            if label == -1:
                # HDBSCAN outlier noise label
                outliers = group_items
                continue

            vectors = np.array(cluster_vectors[label])
            centroid = np.mean(vectors, axis=0)
            centroid = centroid / max(np.linalg.norm(centroid), 1e-12)

            # Compute cosine distances to centroid: 1 - (v . c)
            distances = 1.0 - np.dot(vectors, centroid)

            # Attach distance_score to each item in group
            for item, dist in zip(group_items, distances):
                item["distance_to_centroid"] = float(dist)

            # Sort items by proximity to centroid
            sorted_by_proximity = sorted(group_items, key=lambda x: x.get("distance_to_centroid", 1.0))
            exemplars = sorted_by_proximity[:2]

            clusters_result[int(label)] = {
                "cluster_id": int(label),
                "items": group_items,
                "exemplars": exemplars,
                "centroid": centroid,
                "size": len(group_items),
            }

        return {
            "clusters": clusters_result,
            "outliers": outliers,
            "total_clusters": len(clusters_result),
            "outlier_count": len(outliers)
        }

