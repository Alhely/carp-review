"""Recolector de literatura sobre el Capacitated Arc Routing Problem (CARP).

Consulta la API pública y gratuita de OpenAlex (https://openalex.org), que
indexa a todas las grandes editoriales científicas (Elsevier, IEEE, Springer,
Wiley, Taylor & Francis, etc.). Para cada trabajo recupera:

    - doi
    - title
    - abstract
    - publication_year
    - venue           (revista / conferencia donde se publicó)
    - publisher
    - is_open_access  (True / False)
    - oa_status       (gold / green / hybrid / bronze / closed)
    - openalex_id
    - work_type
    - cited_by_count

No descarga los PDF: solo recupera metadatos.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any, Iterable, Iterator

import requests

from classifier import enrich_record

OPENALEX_WORKS_URL = "https://api.openalex.org/works"

# Correo para el "polite pool" de OpenAlex (respuestas más rápidas y estables).
CONTACT_EMAIL = "alelygl@gmail.com"

# Frases de búsqueda: CARP, sus variantes y su metodología. Cada frase se busca
# como coincidencia exacta en título + abstract y luego se unen los resultados
# eliminando duplicados por identificador de OpenAlex.
SEARCH_PHRASES: list[str] = [
    # Núcleo
    "capacitated arc routing problem",
    "capacitated arc routing",
    "arc routing problem",
    # Variantes
    "periodic capacitated arc routing",
    "stochastic arc routing",
    "mixed capacitated arc routing",
    "multi-depot arc routing",
    "multi-objective arc routing",
    "split delivery arc routing",
    "time-dependent arc routing",
    "min-max capacitated arc routing",
    "large-scale capacitated arc routing",
    "windy arc routing",
    "open capacitated arc routing",
    # Metodología (asociada al dominio)
    "arc routing metaheuristic",
    "arc routing heuristic",
    "arc routing genetic algorithm",
    "arc routing memetic algorithm",
    "arc routing ant colony",
    "arc routing tabu search",
    "arc routing exact algorithm",
    "arc routing branch and cut",
]

PER_PAGE = 200
REQUEST_TIMEOUT = 60
SLEEP_BETWEEN_REQUESTS = 0.15  # cortesía con la API


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Reconstruye el texto del abstract a partir del índice invertido de OpenAlex."""
    if not inverted_index:
        return None
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted_index.items():
        for idx in idxs:
            positions.append((idx, word))
    positions.sort(key=lambda pair: pair[0])
    return " ".join(word for _, word in positions)


def fetch_phrase(phrase: str, session: requests.Session) -> Iterator[dict[str, Any]]:
    """Devuelve todos los trabajos que coinciden con una frase, paginando por cursor."""
    cursor = "*"
    while cursor:
        params = {
            "filter": f'title_and_abstract.search:"{phrase}"',
            "per-page": PER_PAGE,
            "cursor": cursor,
            "mailto": CONTACT_EMAIL,
        }
        resp = session.get(OPENALEX_WORKS_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            break
        yield from results

        cursor = data.get("meta", {}).get("next_cursor")
        time.sleep(SLEEP_BETWEEN_REQUESTS)


def extract_record(work: dict[str, Any]) -> dict[str, Any]:
    """Aplana un trabajo de OpenAlex a los campos solicitados."""
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    open_access = work.get("open_access") or {}

    return {
        "doi": (work.get("doi") or "").replace("https://doi.org/", "") or None,
        "title": work.get("title") or work.get("display_name"),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "publication_year": work.get("publication_year"),
        "venue": source.get("display_name"),
        "publisher": source.get("host_organization_name"),
        "is_open_access": open_access.get("is_oa"),
        "oa_status": open_access.get("oa_status"),
        "work_type": work.get("type"),
        "cited_by_count": work.get("cited_by_count"),
        "openalex_id": work.get("id"),
    }


def collect(phrases: Iterable[str] = SEARCH_PHRASES) -> list[dict[str, Any]]:
    """Ejecuta todas las búsquedas y devuelve registros únicos (dedup por id)."""
    seen: dict[str, dict[str, Any]] = {}
    with requests.Session() as session:
        session.headers.update({"User-Agent": f"CARP-review-scraper ({CONTACT_EMAIL})"})
        for phrase in phrases:
            count = 0
            for work in fetch_phrase(phrase, session):
                work_id = work.get("id")
                if not work_id or work_id in seen:
                    continue
                seen[work_id] = extract_record(work)
                count += 1
            print(f"  [{phrase}] -> {count} nuevos (total acumulado: {len(seen)})")
    return list(seen.values())


CSV_FIELDS = [
    "doi",
    "title",
    "publication_year",
    "venue",
    "publisher",
    "is_open_access",
    "oa_status",
    "variants",
    "solution_approach",
    "metaheuristics",
    "exact_methods",
    "constructive_heuristics",
    "is_hybrid",
    "work_type",
    "cited_by_count",
    "openalex_id",
    "abstract",
]


def save(records: list[dict[str, Any]], out_dir: Path) -> tuple[Path, Path]:
    """Guarda los resultados en CSV y JSON. Devuelve las rutas creadas."""
    out_dir.mkdir(parents=True, exist_ok=True)
    records = sorted(records, key=lambda r: (r.get("publication_year") or 0), reverse=True)

    json_path = out_dir / "carp_articles.json"
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = out_dir / "carp_articles.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field) for field in CSV_FIELDS})

    return csv_path, json_path


def run(out_dir: Path | None = None) -> list[dict[str, Any]]:
    out_dir = out_dir or (Path(__file__).resolve().parent.parent / "data")
    print("Recolectando literatura sobre CARP desde OpenAlex...\n")
    records = collect()
    print("Clasificando variantes y métodos de solución...")
    records = [enrich_record(r) for r in records]
    csv_path, json_path = save(records, out_dir)
    print(f"\nListo. {len(records)} artículos únicos.")
    print(f"  CSV : {csv_path}")
    print(f"  JSON: {json_path}")
    return records


if __name__ == "__main__":
    run()
