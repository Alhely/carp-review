"""Analysis and visualisation of the LLM-classified CARP corpus.

Reads data/carp_articles_llm.json and produces:
  - data/figures/*.png  : figures (per year, variants, approaches, methods, OA)
  - data/crosstab_variante_enfoque.csv : variant x approach cross-tabulation

Usage:
    python src/analysis.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from label_translations import tr_approach, tr_meta, tr_variant

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FIG_DIR = DATA_DIR / "figures"


def load() -> pd.DataFrame:
    records = json.loads((DATA_DIR / "carp_articles_llm.json").read_text(encoding="utf-8"))
    df = pd.DataFrame(records)
    df["publication_year"] = pd.to_numeric(df["publication_year"], errors="coerce")
    return df


def barh(counter: Counter, title: str, xlabel: str, path: Path, top: int | None = None) -> None:
    items = counter.most_common(top)
    labels = [k for k, _ in items][::-1]
    values = [v for _, v in items][::-1]
    plt.figure(figsize=(9, max(3, 0.42 * len(labels))))
    plt.barh(labels, values, color="#4C72B0")
    for i, v in enumerate(values):
        plt.text(v, i, f" {v}", va="center", fontsize=8)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = load()

    # Translate Spanish labels from the LLM classification to English before plotting.
    df["llm_variant"] = df["llm_variant"].map(tr_variant)
    df["llm_approach"] = df["llm_approach"].map(tr_approach)

    rel = df[df["llm_approach"] != "Not relevant"].copy()

    # 1. Publications per year (full corpus, 1981–2026)
    years = df["publication_year"].dropna()
    yr = years[(years >= 1981) & (years <= 2026)].astype(int)
    counts = yr.value_counts().sort_index()
    plt.figure(figsize=(11, 4))
    plt.bar(counts.index, counts.values, color="#55A868")
    plt.title("CARP publications per year")
    plt.xlabel("Year")
    plt.ylabel("Number of articles")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "articulos_por_anio.png", dpi=130)
    plt.close()

    # 2. CARP variants
    barh(Counter(rel["llm_variant"]), "CARP variants (LLM classification)",
         "Number of articles", FIG_DIR / "variantes.png")

    # 3. Solution approach
    barh(Counter(rel["llm_approach"]), "Solution approach",
         "Number of articles", FIG_DIR / "enfoques.png")

    # 4. Specific metaheuristics (top 15)
    mc: Counter = Counter()
    for s in rel["llm_metaheuristics"].fillna(""):
        for m in filter(None, s.split("; ")):
            mc[tr_meta(m)] += 1
    barh(mc, "Most used metaheuristics", "Number of articles",
         FIG_DIR / "metaheuristicas.png", top=15)

    # 5. Open access
    oa = df["is_open_access"].map({True: "Open access", False: "Closed access"}).fillna("Unknown")
    barh(Counter(oa), "Open access vs. closed access", "Number of articles",
         FIG_DIR / "open_access.png")

    # 6. Variant × approach cross-tabulation
    ct = pd.crosstab(rel["llm_variant"], rel["llm_approach"])
    ct["TOTAL"] = ct.sum(axis=1)
    ct = ct.sort_values("TOTAL", ascending=False)
    ct.to_csv(DATA_DIR / "crosstab_variante_enfoque.csv", encoding="utf-8")

    # 7. Evolution of solution approach by year (stacked, 2005+)
    rec = rel.dropna(subset=["publication_year"]).copy()
    rec = rec[rec["publication_year"] >= 2005]
    rec["publication_year"] = rec["publication_year"].astype(int)
    pivot = pd.crosstab(rec["publication_year"], rec["llm_approach"])
    pivot.plot(kind="bar", stacked=True, figsize=(12, 5), colormap="tab10", width=0.85)
    plt.title("Evolution of solution approach by year (2005+)")
    plt.xlabel("Year")
    plt.ylabel("Number of articles")
    plt.legend(title="Approach", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "enfoques_por_anio.png", dpi=130)
    plt.close()

    print("Analysis complete:")
    for p in sorted(FIG_DIR.glob("*.png")):
        print(f"  fig  {p.relative_to(DATA_DIR.parent)}")
    print(f"  csv  {(DATA_DIR / 'crosstab_variante_enfoque.csv').relative_to(DATA_DIR.parent)}")
    print("\nVariant x approach cross-tabulation (relevant records only):")
    print(ct.to_string())


if __name__ == "__main__":
    main()
