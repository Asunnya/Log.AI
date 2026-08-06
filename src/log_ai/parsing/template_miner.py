from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, TypedDict

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig


class TemplateRecord(TypedDict):
    """Schema de cada registro gravado no arquivo JSONL."""

    line_number: int
    raw_line: str
    cluster_id: int
    template: str
    change_type: str


_REQUIRED_RESULT_KEYS = frozenset(
    {
        "cluster_id",
        "template_mined",
        "change_type",
    }
)


def mine_templates(
    log_path: Path,
    config_path: Path,
    output_path: Path,
) -> None:
    """Extrai templates de logs com Drain3 e os persiste em JSONL.

    Entrada:
        log_path: arquivo de logs, com um evento por linha.
        config_path: arquivo ``drain3.ini`` usado pelo TemplateMiner.
        output_path: arquivo JSONL que será criado ou sobrescrito.

    Saída:
        A função retorna ``None``. Para cada linha não vazia do log, grava
        imediatamente um objeto JSON com o schema de ``TemplateRecord``.

    Raises:
        FileNotFoundError: se o arquivo de log ou de configuração não existir.
        IsADirectoryError: se um caminho de entrada apontar para um diretório.
        KeyError: se o Drain3 retornar um resultado com schema inesperado.
    """
    _validate_input_file(log_path, description="arquivo de log")
    _validate_input_file(config_path, description="configuração do Drain3")
    _validate_distinct_output_path(log_path, config_path, output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = TemplateMinerConfig()
    config.load(str(config_path))
    config.profiling_enabled = True

    template_miner = TemplateMiner(config=config)

    processed_lines = 0
    skipped_empty_lines = 0

    with (
        log_path.open("r", encoding="utf-8") as log_file,
        output_path.open("w", encoding="utf-8") as output_file,
    ):
        for line_number, line in enumerate(log_file, start=1):
            raw_line = line.strip()

            if not raw_line:
                skipped_empty_lines += 1
                continue

            result = template_miner.add_log_message(raw_line)
            record = _build_record(
                line_number=line_number,
                raw_line=raw_line,
                result=result,
            )

            output_file.write(json.dumps(record, ensure_ascii=False))
            output_file.write("\n")
            processed_lines += 1

    cluster_count = len(template_miner.drain.clusters)
    print(
        f"{processed_lines} linhas processadas; "
        f"{skipped_empty_lines} linhas vazias ignoradas; "
        f"{cluster_count} clusters"
    )


def _build_record(
    *,
    line_number: int,
    raw_line: str,
    result: Mapping[str, Any],
) -> TemplateRecord:
    missing_keys = _REQUIRED_RESULT_KEYS.difference(result)

    if missing_keys:
        available_keys = ", ".join(sorted(result))
        missing_keys_text = ", ".join(sorted(missing_keys))
        raise KeyError(
            "O resultado retornado por TemplateMiner.add_log_message() "
            f"não contém as chaves esperadas: {missing_keys_text}. "
            f"Chaves disponíveis: {available_keys or '<nenhuma>'}."
        )

    return TemplateRecord(
        line_number=line_number,
        raw_line=raw_line,
        cluster_id=int(result["cluster_id"]),
        template=str(result["template_mined"]),
        change_type=str(result["change_type"]),
    )


def _validate_input_file(path: Path, *, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{description.capitalize()} não encontrado: {path}")

    if not path.is_file():
        raise IsADirectoryError(f"{description.capitalize()} não é um arquivo: {path}")


def _validate_distinct_output_path(
    log_path: Path,
    config_path: Path,
    output_path: Path,
) -> None:
    resolved_output_path = output_path.resolve()

    for input_path in (log_path, config_path):
        if resolved_output_path == input_path.resolve():
            raise ValueError(
                "output_path não pode sobrescrever um arquivo de entrada: "
                f"{output_path}"
            )