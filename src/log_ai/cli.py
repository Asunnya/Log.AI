from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from log_ai.llm.client import LLMClient
from log_ai.parsing.config_inference import update_drain3_ini, infer_drain_config
from log_ai.parsing.template_miner import mine_templates

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Infer a Drain3 masking configuration from log samples"
    )

    parser.add_argument(
        "input_file",
        type=Path, 
        help="Text file containing one log sample per line.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Existing Drain3 INI configuration file to update.",
    )

    parser.add_argument(
        "--template-output", type=Path, default=Path("data/templates.jsonl", help="template output path")
    )

    return parser.parse_args()

def main() -> None:
    load_dotenv()
    arguments = parse_arguments()
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

if __name__ == "__main__":
    main()
