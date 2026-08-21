from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from log_ai.llm.client import LLMClient
from log_ai.parsing.config_inference import update_drain3_ini, infer_drain_config
from log_ai.parsing.template_miner import mine_templates
from log_ai.embedding.grouping import load_template_records, group_by_template, write_template_groups, load_template_groups
from log_ai.embedding.embedder import build_template_embeddings
from log_ai.embedding.clustering import assign_semantic_cluster
from log_ai.router.taxonomy_discovery import agreggated_semantic_cluster, write_aggregated_semantic_cluster
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Infer a Drain3 masking configuration from log samples"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    # -------------------------
    # comando: mine
    # -------------------------

    parser_mine = subparsers.add_parser("mine")

    parser_mine.add_argument(
        "input_file",
        type=Path, 
        help="Text file containing one log sample per line.",
    )
    parser_mine.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Existing Drain3 INI configuration file to update.",
    )

    parser_mine.add_argument(
        "--template-output", type=Path, 
        default=Path("data/templates.jsonl"), 
        help="template output path"
    )

    # -------------------------
    # comando: group
    # -------------------------
    parser_group = subparsers.add_parser("group")

    parser_group.add_argument(
        "template_path",
        type=Path, 
        help="caminho para template.jsonl",
    )
    parser_group.add_argument(
        "--group-output", type=Path, 
        default=Path("data/template_groups.jsonl"), 
        help="template group output path"
    )

    # -------------------------
    # comando: embed
    # -------------------------

    parser_embed = subparsers.add_parser("embed")
    parser_embed.add_argument(
        "group_path", 
        type=Path, 
        help="caminho para TemplatesGroup.jsonl",
    )
    parser_embed.add_argument(
        "--embed-output", type=Path, 
        default=Path("data/embeddings.npy"), 
        help="template group output path"
    )


    # -------------------------
    # comando: cluster
    # -------------------------

    parser_cluster = subparsers.add_parser("cluster")
    parser_cluster.add_argument(
        "group_path", 
        type=Path, 
        help="caminho para TemplatesGroup.jsonl",
    )
    parser_cluster.add_argument(
        "embed_path", type=Path, 
        help="Input path for embeddings path"
    )    
    
    parser_cluster.add_argument(
        "--min-cluster-size", type=int,
        default=5,
        help="min size to cluster"
    )

    # -------------------------
    # comando: aggregate
    # -------------------------

    parser_aggregate = subparsers.add_parser("aggregate")
    parser_aggregate.add_argument(
        "group_path", 
        type=Path, 
        help="caminho para TemplatesGroup.jsonl",
    )
    parser_aggregate.add_argument(
        "--summary-output", type=Path, 
        default=Path("data/cluster_summaries.json"), 
        help="Output cluster summary"
    )

    
    return parser.parse_args()


def _run_group(arguments: argparse.Namespace) -> None:
    
    json_data = load_template_records(arguments.template_path)
    groups = group_by_template(json_data)
    write_template_groups(groups, arguments.group_output)


def _run_embed(arguments: argparse.Namespace) -> None: 
    model_embed = os.getenv("EMBED_MODEL")
    if not model_embed:
        raise RuntimeError(
            "Environment variable EMBED_MODEL is not configured."
        )

    build_template_embeddings(arguments.group_path, arguments.embed_output, model_embed)

def _run_cluster(arguments: argparse.Namespace) -> None:
    assign_semantic_cluster(arguments.group_path, arguments.embed_path, arguments.min_cluster_size)


def _run_aggregate(arguments: argparse.Namespace) ->  None:
    clusters  = agreggated_semantic_cluster(load_template_groups(arguments.group_path))
    write_aggregated_semantic_cluster(clusters, arguments.summary_output)



def _run_mine(arguments: argparse.Namespace) -> None:
    model = os.getenv("LLM_MODEL")
    if not model:
        raise RuntimeError(
            "Environment variable LLM_MODEL is not configured."
        )

    client = LLMClient(
        model=model, 
        temperature= float(
            os.getenv("LLM_TEMPERATURE", "0.1")
        )
    )

    log_lines = arguments.input_file.read_text(
        encoding="utf-8"
    ).splitlines()

    config = infer_drain_config(
        client=client,
        log_lines=log_lines
    )

    update_drain3_ini(
        ini_path=arguments.config,
        config=config
    )


    print(config.model_dump_json(indent=2))
    print(f"Configuration updated in: {arguments.config}")

    mine_templates(log_path=arguments.input_file, config_path=arguments.config, output_path=arguments.template_output)
    print(f"Templates saved in: {arguments.template_output}")

def main() -> None:
    commands = {
        "mine": _run_mine,
        "group": _run_group,
        "embed": _run_embed,
        "cluster": _run_cluster, 
        "aggregate": _run_aggregate
    }

    load_dotenv()
    arguments = parse_arguments()
  

    commands[arguments.command](arguments)


if __name__ == "__main__":
    main()
