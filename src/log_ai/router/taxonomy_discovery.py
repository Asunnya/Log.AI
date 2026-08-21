
from __future__ import annotations


from log_ai.embedding.grouping import TemplateGroup
from pathlib import Path 
import json

from dataclasses import dataclass
from dataclasses import asdict 


@dataclass
class ClusterSummary:
    semantic_cluster: int 
    count: int 
    representative_template : str 

def write_aggregated_semantic_cluster(clusters: list[ClusterSummary], output_path: Path) -> None:
    clusters_json = [asdict(c) for c in clusters]
    with(output_path.open("w", encoding="utf-8") as output_file):
        json.dump(clusters_json, output_file, ensure_ascii=False, indent=2)


def agreggated_semantic_cluster(groups: list[TemplateGroup]) -> list[ClusterSummary]:
    aggregated_final = dict()

    for group in groups:
        if group.semantic_cluster == -1:
            #dont use
            pass
        else:
            aggregated_final.setdefault(group.semantic_cluster, []).append(group)
    
    aggregated_final_sum = { key: sum(v.count for v in val) for key, val in aggregated_final.items() }

    maior = {
        key: max(val, key=lambda g: g.count) for key, val in aggregated_final.items()
    }

    result = []

    for k in aggregated_final_sum:
        cluster = ClusterSummary(
            semantic_cluster=k,
            count=aggregated_final_sum[k],
            representative_template = maior[k].template
        )

        result.append(cluster)
    
    return result
    