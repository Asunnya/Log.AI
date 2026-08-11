from __future__ import annotations
from pathlib import Path 

from sentence_transformers import SentenceTransformer 
from log_ai.embedding.grouping import load_template_groups
from collections.abc import Sequence 

import numpy as np 

def embed_templates(templates: Sequence[str], model_name: str) -> np.ndarray:
    model = SentenceTransformer(model_name)
    return model.encode(templates)



def build_template_embeddings(groups_path: Path, output_path:Path, model_name:str) -> None:
    groups = load_template_groups(groups_path)
    templates = [group.template for group in groups]
    embeddings = embed_templates(templates=templates, model_name=model_name)
    np.save(output_path, embeddings)

