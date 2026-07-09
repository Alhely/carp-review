"""Clasificación de artículos de CARP mediante un LLM (Claude).

A diferencia de `classifier.py` (reglas por palabras clave), este módulo lee el
título + abstract de cada artículo y pide a Claude que determine, con juicio
semántico, la variante del CARP y cómo se resolvió. Devuelve un único método
"principal" bien desambiguado por artículo, en lugar de sobre-etiquetar.

Usa la Batch API de Anthropic (50% más barata, pensada para lotes grandes) y
structured outputs (esquema JSON) para que la respuesta sea siempre parseable.

Requisitos:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...

Uso:
    python src/llm_classifier.py            # clasifica los que tienen abstract
    python src/llm_classifier.py --limit 20 # prueba con 20 artículos
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INPUT_JSON = DATA_DIR / "carp_articles.json"
OUTPUT_JSON = DATA_DIR / "carp_articles_llm.json"
OUTPUT_CSV = DATA_DIR / "carp_articles_llm.csv"

MODEL = "claude-haiku-4-5"
MAX_TOKENS = 1024

# Esquema de la clasificación que exigimos al modelo.
VARIANT_ENUM = [
    "CARP clásico",
    "Periódico (PCARP)",
    "Estocástico / Incierto",
    "Mixto (MCARP)",
    "Multi-depósito",
    "Multi-objetivo",
    "Min-max / Balanceado",
    "Split-delivery",
    "Dinámico / Time-dependent",
    "Con ventanas de tiempo (CARPTW)",
    "Windy (WARP)",
    "Abierto (OCARP)",
    "Prize-collecting / Profitable",
    "Con instalaciones intermedias (CLARPIF)",
    "Green / Eléctrico",
    "Large-scale",
    "Otra variante",
    "No es CARP (RPP/CPP/otro)",
]

APPROACH_ENUM = [
    "Exacto",
    "Heurística constructiva",
    "Metaheurística",
    "Híbrido / Matheurística",
    "Aprendizaje / ML",
    "Survey / Teórico / Modelado",
    "No especificado",
]

RELEVANCE_ENUM = ["CARP núcleo", "Variante de CARP", "Arc routing relacionado", "No relevante"]

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "relevance": {"type": "string", "enum": RELEVANCE_ENUM},
        "carp_variant": {"type": "string", "enum": VARIANT_ENUM},
        "solution_approach": {"type": "string", "enum": APPROACH_ENUM},
        "metaheuristics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Nombres concretos de metaheurísticas usadas (GA, tabu search, ACO, VNS, ALNS...). Vacío si no aplica.",
        },
        "is_hybrid": {"type": "boolean"},
        "how_solved": {
            "type": "string",
            "description": "Una frase en español que resuma cómo se resolvió el problema.",
        },
    },
    "required": [
        "relevance",
        "carp_variant",
        "solution_approach",
        "metaheuristics",
        "is_hybrid",
        "how_solved",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "Eres un experto en optimización combinatoria y en el Capacitated Arc Routing "
    "Problem (CARP). Se te da el título y el abstract de un artículo científico. "
    "Clasifícalo según el esquema, determinando: (1) qué tan relevante es al CARP, "
    "(2) qué variante del CARP aborda, (3) cómo se resolvió (método principal), "
    "(4) qué metaheurísticas concretas usa si aplica, (5) si el enfoque es híbrido, "
    "y (6) una frase resumiendo la resolución. Básate SOLO en el texto dado; si el "
    "abstract no especifica el método, usa 'No especificado'."
)


def build_prompt(record: dict[str, Any]) -> str:
    title = record.get("title") or "(sin título)"
    abstract = record.get("abstract") or "(sin abstract)"
    return f"TÍTULO: {title}\n\nABSTRACT: {abstract}"


def make_requests(records: list[dict[str, Any]]) -> tuple[list[Request], dict[str, dict]]:
    requests: list[Request] = []
    index: dict[str, dict] = {}
    for i, record in enumerate(records):
        custom_id = f"rec-{i}"
        index[custom_id] = record
        requests.append(
            Request(
                custom_id=custom_id,
                params=MessageCreateParamsNonStreaming(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": build_prompt(record)}],
                    output_config={
                        "format": {
                            "type": "json_schema",
                            "schema": OUTPUT_SCHEMA,
                        }
                    },
                ),
            )
        )
    return requests, index


def parse_result_text(message: Any) -> dict[str, Any] | None:
    for block in message.content:
        if block.type == "text":
            try:
                return json.loads(block.text)
            except json.JSONDecodeError:
                return None
    return None


CSV_FIELDS = [
    "doi",
    "title",
    "publication_year",
    "venue",
    "is_open_access",
    "llm_relevance",
    "llm_variant",
    "llm_approach",
    "llm_metaheuristics",
    "llm_is_hybrid",
    "llm_how_solved",
]


def save(records: list[dict[str, Any]]) -> None:
    import csv

    records = sorted(records, key=lambda r: (r.get("publication_year") or 0), reverse=True)
    OUTPUT_JSON.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k) for k in CSV_FIELDS})


def run(limit: int | None = None) -> None:
    client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno

    all_records: list[dict[str, Any]] = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    # Solo clasificamos los que tienen abstract (el LLM necesita texto que analizar).
    to_classify = [r for r in all_records if r.get("abstract")]
    if limit:
        to_classify = to_classify[:limit]

    print(f"Artículos con abstract a clasificar: {len(to_classify)}")
    requests, index = make_requests(to_classify)

    batch = client.messages.batches.create(requests=requests)
    print(f"Batch creado: {batch.id} (estado: {batch.processing_status})")
    print("Procesando (puede tardar minutos; la mayoría termina en <1h)...")

    while True:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        c = batch.request_counts
        print(f"  ... procesando: {c.processing} | ok: {c.succeeded} | error: {c.errored}")
        time.sleep(20)

    print("Batch terminado. Recuperando resultados...")
    ok = err = 0
    for result in client.messages.batches.results(batch.id):
        record = index.get(result.custom_id)
        if record is None:
            continue
        if result.result.type == "succeeded":
            parsed = parse_result_text(result.result.message)
            if parsed:
                record["llm_relevance"] = parsed.get("relevance")
                record["llm_variant"] = parsed.get("carp_variant")
                record["llm_approach"] = parsed.get("solution_approach")
                record["llm_metaheuristics"] = "; ".join(parsed.get("metaheuristics", []))
                record["llm_is_hybrid"] = parsed.get("is_hybrid")
                record["llm_how_solved"] = parsed.get("how_solved")
                ok += 1
            else:
                err += 1
        else:
            err += 1

    save(to_classify)
    print(f"\nListo. Clasificados OK: {ok} | con error: {err}")
    print(f"  CSV : {OUTPUT_CSV}")
    print(f"  JSON: {OUTPUT_JSON}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Clasificar solo los primeros N (para pruebas)")
    args = ap.parse_args()
    run(limit=args.limit)
