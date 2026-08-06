# Log.AI

Pipeline multi-agente para triagem automática de logs de produção, usando datasets reais do
[LogHub](https://github.com/logpai/loghub) como base de teste.

## Arquitetura

O pipeline é dividido em 5 etapas:

1. **Parser/Normalizer** — infere uma configuração de masking do Drain3 via LLM a partir de
   amostras de log, atualiza o `.ini` de configuração, e minera templates estruturais dos logs
   brutos usando o [Drain3](https://github.com/logpai/Drain3).
2. **Embedding + Clustering** — embeda os templates minerados e agrupa eventos semanticamente
   similares (HDBSCAN).
3. **Router** — uma chamada ao modelo decide, por cluster, qual tipo de investigação é
   necessária.
4. **Sub-agentes de diagnóstico** — agentes especializados, rodando em paralelo, investigam
   cada cluster roteado usando ferramentas.
5. **Aggregator** — consolida os diagnósticos num relatório de incidente ranqueado.

**Status atual:** Etapa 1 completa. Etapas 2 a 5 ainda não implementadas.

## Setup

```bash
uv sync
```

Crie um arquivo `.env` na raiz do projeto com:

```
ANTHROPIC_API_KEY=<sua chave>
LLM_MODEL=<modelo usado para inferência de config, ex: anthropic/claude-haiku-4-5>
LLM_TEMPERATURE=<opcional, default 0.1>
```

## Uso (Etapa 1)

```bash
uv run log-ai <arquivo_de_log> --config <caminho_para_drain3.ini> [--templates-output <caminho_saida.jsonl>]
```

- `<arquivo_de_log>`: arquivo de texto com um evento de log por linha.
- `--config`: arquivo `.ini` de configuração do Drain3, já existente, que será atualizado
  (apenas a seção `[MASKING]`) com a config inferida pelo LLM a partir das amostras do log.
- `--templates-output`: caminho do JSONL de saída com os templates minerados
  (default: `data/templates.jsonl`).

## Estrutura do projeto

```
src/log_ai/
├── cli.py              # orquestração da Etapa 1
├── llm/
│   ├── client.py        # client LLM genérico (litellm + validação estruturada via pydantic)
│   └── models.py         # schemas pydantic (DrainConfig, MaskingInstruction)
└── parsing/
    ├── config_inference.py  # infere e atualiza a config de masking do Drain3 via LLM
    └── template_miner.py    # roda o Drain3 e persiste templates minerados em JSONL
```
