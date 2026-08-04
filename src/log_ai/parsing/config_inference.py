
from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

from dotenv import load_dotenv

from log_ai.llm.client import LLMClient
from log_ai.llm.models import DrainConfig



SYSTEM_PROMPT = """
You infer Drain3 masking configurations from representative log samples.

Your task is to identify variable portions of the logs that should be masked
before Drain3 performs template mining.

Rules:

1. Each masking instruction must contain:
   - regex_pattern: a valid Python regular expression.
   - mask_with: a concise uppercase semantic identifier.

2. Prefer semantic identifiers such as:
   IP, IPV6, UUID, URL, EMAIL, PATH, TIMESTAMP, DATE, TIME, PORT, PID, NUM.

3. Do not mask stable words that identify the event itself.

4. Avoid overly broad expressions such as .* or \\S+ when a more specific
   expression can be created.

5. Do not include regex delimiters such as /pattern/.

6. Avoid duplicate or overlapping masking instructions unless they represent
   genuinely different data types.

7. Use "<" as mask_prefix and ">" as mask_suffix unless the log samples
   clearly require different delimiters.
""".strip()


def infer_drain_config(
    client: LLMClient, 
    log_lines: Sequence[str],
) -> DrainConfig:
    normalized_lines = [line.strip() for line in log_lines if line.strip()]

    if not normalized_lines:
        raise ValueError("At least one non empty log line is required.")
    
    formatted_samples = "\n".join(
        f"{index}. {line}"
        for index, line in enumerate(normalized_lines, start=1)
    )


    user_prompt = f"""
        Analyze the following log samples and infer an appropriate Drain3 masking
        configuration.

        <log_samples>
        {formatted_samples}
        </log_samples>
    """.strip()

    messages = [
        client.system_message(SYSTEM_PROMPT), 
        client.user_message(user_prompt)
    ]

    return client.complete(
        messages=messages,
        response_schema=DrainConfig
    )


def render_drain3_masking_section(config: DrainConfig)-> str:

    masking_data = [
        instruction.model_dump()
        for instruction in config.masking
    ]

    masking_json = json.dumps(
        masking_data,
        ensure_ascii=False, 
        indent=2,
    )

    indented_masking_json = masking_json.replace("\n", "\n      ")

    return (
        "[MASKING]\n"
        f"masking = {indented_masking_json}\n"
        f"mask_prefix = {config.mask_prefix}\n"
        f"mask_suffix = {config.mask_suffix}\n"
    )

