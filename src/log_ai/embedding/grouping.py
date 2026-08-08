
from __future__ import annotations

from typing import  TypedDict
from pathlib import Path 
from collections.abc import Iterable
import json 
from log_ai.parsing.template_miner import TemplateRecord
from dataclasses import dataclass, field
from dataclasses import asdict 



@dataclass
class TemplateGroup:
    template: str 
    cluster_ids : list[int] = field(default_factory=list)

    line_numbers: list[int] = field(default_factory=list)
    count: int  = 0 


def load_template_records(path: Path) -> list[TemplateRecord]:
    # LE template.jsonl linha por linha e carrega 
    json_data = []
    with open(path) as data:
        for line in data:
            parsed = json.loads(line)
            json_data.append(TemplateRecord(**parsed))
    return json_data

def group_by_template (records: Iterable[TemplateRecord])-> list[TemplateGroup]:
    #agrupa por igualdade exata da string template acumulando cluster_id e line number sem duplicar 
    template_dict: dict[str, dict]  = {}
    listTG = []
    for record in records:
        t = record.template
        if not t in template_dict:
            template_dict[t] = {"cluster_ids": {record.cluster_id}, "line_numbers": {record.line_number}, "count": 1}
        else:
            template_dict[t]["count"] =  int(template_dict[t]["count"]) + 1
            template_dict[t]["cluster_ids"].add(record.cluster_id)
            template_dict[t]["line_numbers"].add(record.line_number)

    for template, data in template_dict.items():
        objeto = TemplateGroup(
            template=template,
            cluster_ids=list(data["cluster_ids"]),
            line_numbers=list(data["line_numbers"]),
            count=data["count"]
        )
        listTG.append(objeto)

    return listTG

def write_template_groups(groups: list[TemplateGroup], output_path: Path) -> None:
    """Extrai templates agrupados e os persiste em JSONL.

    Entrada:
        groups: lista de templates agrupados pelo groupbytemplate
        output_path: arquivo JSONL que será criado ou sobrescrito.

    Saída:
        A função retorna ``None``.

    """

    with(output_path.open("w", encoding="utf-8") as output_file):
        for group in groups:
            output_file.write(json.dumps(asdict(group), ensure_ascii=False) + "\n")