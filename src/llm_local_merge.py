"""Fusiona las clasificaciones LLM locales en el CSV/JSON final.

Lee todos los lotes scratchpad de resultados (data/llm_results/*.json), cada uno
una lista de objetos {"i", "relevance", "variant", "approach", "metaheuristics",
"is_hybrid", "how_solved"}, y los une con los artículos-con-abstract por índice.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESULTS_DIR = DATA_DIR / "llm_results"

CSV_FIELDS = [
    "doi", "title", "publication_year", "venue", "is_open_access",
    "llm_relevance", "llm_variant", "llm_approach",
    "llm_metaheuristics", "llm_is_hybrid", "llm_how_solved",
]


def main() -> None:
    records = json.loads((DATA_DIR / "carp_articles.json").read_text(encoding="utf-8"))
    with_abs = [r for r in records if r.get("abstract")]

    by_index: dict[int, dict] = {}
    for f in sorted(RESULTS_DIR.glob("*.json")):
        for item in json.loads(f.read_text(encoding="utf-8")):
            by_index[item["i"]] = item

    classified = 0
    for i, r in enumerate(with_abs):
        c = by_index.get(i)
        if not c:
            continue
        r["llm_relevance"] = c.get("relevance")
        r["llm_variant"] = c.get("variant")
        r["llm_approach"] = c.get("approach")
        mh = c.get("metaheuristics") or []
        r["llm_metaheuristics"] = "; ".join(mh) if isinstance(mh, list) else str(mh)
        r["llm_is_hybrid"] = c.get("is_hybrid")
        r["llm_how_solved"] = c.get("how_solved")
        classified += 1

    out = sorted(with_abs, key=lambda r: (r.get("publication_year") or 0), reverse=True)
    (DATA_DIR / "carp_articles_llm.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    with (DATA_DIR / "carp_articles_llm.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in out:
            w.writerow({k: r.get(k) for k in CSV_FIELDS})

    print(f"Fusionados {classified}/{len(with_abs)} artículos.")
    print(f"  CSV : {DATA_DIR / 'carp_articles_llm.csv'}")
    print(f"  JSON: {DATA_DIR / 'carp_articles_llm.json'}")


if __name__ == "__main__":
    main()
