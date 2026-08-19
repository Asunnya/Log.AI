from __future__ import annotations


from sklearn.preprocessing import normalize
from sklearn.cluster import HDBSCAN
from pathlib import Path 
from log_ai.embedding.grouping import load_template_groups, write_template_groups
import numpy as np 


def cluster_embeddings(embeddings: np.ndarray, min_cluster_size: int) -> np.ndarray: 
    embeddings_normalized = normalize(embeddings, "l2")
    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean"
    )

    labels = clusterer.fit_predict(embeddings_normalized)

    return labels


def assign_semantic_cluster(groups_path: Path, embeddings_path: Path, min_cluster_size: int) -> None:
    groups = load_template_groups(groups_path)
    embeddings = np.load(embeddings_path)
    labels = cluster_embeddings(embeddings, min_cluster_size)
    
    if len(groups) != len(labels):
      raise ValueError(
          f"groups ({len(groups)}) e embeddings ({len(labels)}) fora de sincronia"
      )
    
    for group, label in zip(groups, labels):
        group.semantic_cluster = int(label)

    write_template_groups(groups, groups_path)
        