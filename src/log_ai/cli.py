from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from log_ai.llm.client import LLMClient
from log_ai.llm.config_inference import render_drain3_masking_section, infer_drain_config

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
        "--output",
        type=Path, 
        default=Path("drain_masking.ini"), 
        help="Destination DRain3 INI file.",
    )

    return parser.parse_args()

def main() -> None:
    load_dotenv()
    arguments = parse_arguments()
    model = os.environ("LLM_MODEL")

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

    ini_content = render_drain3_masking_section(config)

    arguments.output.write_text(
        ini_content,
        encoding="utf-8"
    )

    print(config.model_dump_json(indent=2))
    print(f"Configuration written to: {arguments.output}")

if __name__ == "__main__":
    main()
