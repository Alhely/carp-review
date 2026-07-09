"""Reprocesa data/carp_articles.json añadiendo variante y método de solución.

Úsalo para clasificar datos ya recolectados sin volver a consultar OpenAlex.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from carp_scraper import save
from classifier import enrich_record

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    json_path = DATA_DIR / "carp_articles.json"
    records = json.loads(json_path.read_text(encoding="utf-8"))

    records = [enrich_record(r) for r in records]
    csv_path, json_path = save(records, DATA_DIR)

    n = len(records)
    print(f"Enriquecidos {n} artículos.\n")

    print("== Enfoque de solución ==")
    for approach, c in Counter(r["solution_approach"] for r in records).most_common():
        print(f"  {c:4d}  {approach}")

    print("\n== Metaheurísticas más usadas ==")
    meta_counter: Counter = Counter()
    for r in records:
        for m in filter(None, r["metaheuristics"].split("; ")):
            meta_counter[m] += 1
    for m, c in meta_counter.most_common(15):
        print(f"  {c:4d}  {m}")

    print("\n== Variantes del CARP ==")
    var_counter: Counter = Counter()
    for r in records:
        for v in filter(None, r["variants"].split("; ")):
            var_counter[v] += 1
    for v, c in var_counter.most_common(20):
        print(f"  {c:4d}  {v}")

    print(f"\n  CSV : {csv_path}")
    print(f"  JSON: {json_path}")


if __name__ == "__main__":
    main()
