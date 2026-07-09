"""Filter the already-collected corpus to works published from 2021 onward.

Does not re-query OpenAlex or re-classify: reuses the previously generated
files (carp_articles*.json) and writes filtered copies with the prefix
2021on_, regenerating figures and the cross-tabulation for that subset.

Produces:
  - data/2021on_carp_articles.{json,csv}       (metadata + rule-based labels)
  - data/2021on_carp_articles_llm.{json,csv}    (with llm_* columns)
  - data/2021on_figures/*.png
  - data/2021on_crosstab_variante_enfoque.csv

Usage:
    python src/filter_2021on.py
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from label_translations import tr_approach, tr_meta, tr_variant

MIN_YEAR = 2021
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FIG_DIR = DATA_DIR / "2021on_figures"

BASE_CSV_FIELDS = [
    "doi", "title", "publication_year", "venue", "publisher",
    "is_open_access", "oa_status", "variants", "solution_approach",
    "metaheuristics", "exact_methods", "constructive_heuristics",
    "is_hybrid", "work_type", "cited_by_count", "openalex_id", "abstract",
]
LLM_CSV_FIELDS = [
    "doi", "title", "publication_year", "venue", "is_open_access",
    "llm_relevance", "llm_variant", "llm_approach",
    "llm_metaheuristics", "llm_is_hybrid", "llm_how_solved",
]


def _recent(records: list[dict]) -> list[dict]:
    return [r for r in records if (r.get("publication_year") or 0) >= MIN_YEAR]


def _write_csv(records: list[dict], fields: list[str], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in records:
            w.writerow({k: r.get(k) for k in fields})


def filter_files() -> tuple[list[dict], list[dict]]:
    base = json.loads((DATA_DIR / "carp_articles.json").read_text(encoding="utf-8"))
    llm = json.loads((DATA_DIR / "carp_articles_llm.json").read_text(encoding="utf-8"))

    base_r = _recent(base)
    llm_r = _recent(llm)

    (DATA_DIR / "2021on_carp_articles.json").write_text(
        json.dumps(base_r, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(base_r, BASE_CSV_FIELDS, DATA_DIR / "2021on_carp_articles.csv")

    (DATA_DIR / "2021on_carp_articles_llm.json").write_text(
        json.dumps(llm_r, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(llm_r, LLM_CSV_FIELDS, DATA_DIR / "2021on_carp_articles_llm.csv")

    print(f"Full corpus -> {len(base)} works; from {MIN_YEAR}: {len(base_r)}")
    print(f"With abstract (LLM) -> {len(llm)} works; from {MIN_YEAR}: {len(llm_r)}")
    return base_r, llm_r


def barh(counter: Counter, title: str, path: Path, top: int | None = None) -> None:
    items = counter.most_common(top)
    labels = [k for k, _ in items][::-1]
    values = [v for _, v in items][::-1]
    plt.figure(figsize=(9, max(3, 0.42 * len(labels))))
    plt.barh(labels, values, color="#4C72B0")
    for i, v in enumerate(values):
        plt.text(v, i, f" {v}", va="center", fontsize=8)
    plt.title(title)
    plt.xlabel("Number of articles")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def analyze(base_r: list[dict], llm_r: list[dict]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(base_r)
    df["publication_year"] = pd.to_numeric(df["publication_year"], errors="coerce")

    rel = pd.DataFrame(llm_r)
    # Translate Spanish labels to English before any plotting or cross-tabulation.
    rel["llm_variant"] = rel["llm_variant"].map(tr_variant)
    rel["llm_approach"] = rel["llm_approach"].map(tr_approach)
    rel = rel[rel["llm_approach"] != "Not relevant"].copy()

    # 1. Publications per year (2021+)
    yr = df["publication_year"].dropna().astype(int)
    counts = yr[yr >= MIN_YEAR].value_counts().sort_index()
    plt.figure(figsize=(8, 4))
    plt.bar(counts.index.astype(str), counts.values, color="#55A868")
    for x, v in zip(range(len(counts)), counts.values):
        plt.text(x, v, str(v), ha="center", va="bottom", fontsize=9)
    plt.title(f"CARP publications per year ({MIN_YEAR}+)")
    plt.xlabel("Year")
    plt.ylabel("Number of articles")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "2021on_articulos_por_anio.png", dpi=130)
    plt.close()

    # 2. CARP variants
    barh(Counter(rel["llm_variant"]), f"CARP variants ({MIN_YEAR}+)",
         FIG_DIR / "2021on_variantes.png")

    # 3. Solution approach
    barh(Counter(rel["llm_approach"]), f"Solution approach ({MIN_YEAR}+)",
         FIG_DIR / "2021on_enfoques.png")

    # 4. Specific metaheuristics (top 15)
    mc: Counter = Counter()
    for s in rel["llm_metaheuristics"].fillna(""):
        for m in filter(None, s.split("; ")):
            mc[tr_meta(m)] += 1
    barh(mc, f"Most used metaheuristics ({MIN_YEAR}+)",
         FIG_DIR / "2021on_metaheuristicas.png", top=15)

    # 5. Open access
    oa = df["is_open_access"].map({True: "Open access", False: "Closed access"}).fillna("Unknown")
    barh(Counter(oa), f"Open access vs. closed access ({MIN_YEAR}+)",
         FIG_DIR / "2021on_open_access.png")

    # 6. Variant × approach cross-tabulation
    ct = pd.crosstab(rel["llm_variant"], rel["llm_approach"])
    ct["TOTAL"] = ct.sum(axis=1)
    ct = ct.sort_values("TOTAL", ascending=False)
    ct.to_csv(DATA_DIR / "2021on_crosstab_variante_enfoque.csv", encoding="utf-8")

    print("\nFigures and cross-tabulation:")
    for p in sorted(FIG_DIR.glob("*.png")):
        print(f"  fig  {p.relative_to(DATA_DIR.parent)}")
    print(f"  csv  {(DATA_DIR / '2021on_crosstab_variante_enfoque.csv').relative_to(DATA_DIR.parent)}")
    print(f"\nVariant x approach cross-tabulation ({MIN_YEAR}+, relevant records only):")
    print(ct.to_string())


def main() -> None:
    base_r, llm_r = filter_files()
    analyze(base_r, llm_r)


if __name__ == "__main__":
    main()
