"""Filtra el corpus ya generado a los trabajos publicados desde 2021 en adelante.

No vuelve a consultar OpenAlex ni a re-clasificar: reutiliza los archivos ya
producidos (`carp_articles*.json`) y crea copias filtradas con el prefijo
`2021on_`, además de regenerar los gráficos y la tabla cruzada para ese
subconjunto.

Genera:
  - data/2021on_carp_articles.{json,csv}       (metadatos + clasificación por reglas)
  - data/2021on_carp_articles_llm.{json,csv}    (con las columnas llm_*)
  - data/2021on_figures/*.png
  - data/2021on_crosstab_variante_enfoque.csv

Uso:
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

MIN_YEAR = 2021
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FIG_DIR = DATA_DIR / "2021on_figures"

# Columnas de cada CSV (mismas que en los scripts originales).
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

    print(f"Corpus completo -> {len(base)} trabajos; desde {MIN_YEAR}: {len(base_r)}")
    print(f"Con abstract (LLM) -> {len(llm)} trabajos; desde {MIN_YEAR}: {len(llm_r)}")
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
    plt.xlabel("N.º de artículos")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def analyze(base_r: list[dict], llm_r: list[dict]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(base_r)
    df["publication_year"] = pd.to_numeric(df["publication_year"], errors="coerce")
    rel = pd.DataFrame(llm_r)
    rel = rel[rel["llm_relevance"] != "No relevante"].copy()

    # 1. Artículos por año (2021+)
    yr = df["publication_year"].dropna().astype(int)
    counts = yr[yr >= MIN_YEAR].value_counts().sort_index()
    plt.figure(figsize=(8, 4))
    plt.bar(counts.index.astype(str), counts.values, color="#55A868")
    for x, v in zip(range(len(counts)), counts.values):
        plt.text(x, v, str(v), ha="center", va="bottom", fontsize=9)
    plt.title(f"Publicaciones sobre CARP por año ({MIN_YEAR}+)")
    plt.xlabel("Año")
    plt.ylabel("N.º de artículos")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "2021on_articulos_por_anio.png", dpi=130)
    plt.close()

    # 2-5. Distribuciones
    barh(Counter(rel["llm_variant"]), f"Variantes del CARP ({MIN_YEAR}+)",
         FIG_DIR / "2021on_variantes.png")
    barh(Counter(rel["llm_approach"]), f"Enfoque de solución ({MIN_YEAR}+)",
         FIG_DIR / "2021on_enfoques.png")
    mc: Counter = Counter()
    for s in rel["llm_metaheuristics"].fillna(""):
        for m in filter(None, s.split("; ")):
            mc[m] += 1
    barh(mc, f"Metaheurísticas más usadas ({MIN_YEAR}+)",
         FIG_DIR / "2021on_metaheuristicas.png", top=15)
    oa = df["is_open_access"].map({True: "Open access", False: "Acceso cerrado"}).fillna("Desconocido")
    barh(Counter(oa), f"Acceso abierto vs. cerrado ({MIN_YEAR}+)",
         FIG_DIR / "2021on_open_access.png")

    # 6. Tabla cruzada variante x enfoque
    ct = pd.crosstab(rel["llm_variant"], rel["llm_approach"])
    ct["TOTAL"] = ct.sum(axis=1)
    ct = ct.sort_values("TOTAL", ascending=False)
    ct.to_csv(DATA_DIR / "2021on_crosstab_variante_enfoque.csv", encoding="utf-8")

    print("\nGráficos y tabla cruzada:")
    for p in sorted(FIG_DIR.glob("*.png")):
        print(f"  fig  {p.relative_to(DATA_DIR.parent)}")
    print(f"  csv  {(DATA_DIR / '2021on_crosstab_variante_enfoque.csv').relative_to(DATA_DIR.parent)}")
    print(f"\nTabla cruzada variante x enfoque ({MIN_YEAR}+, relevantes):")
    print(ct.to_string())


def main() -> None:
    base_r, llm_r = filter_files()
    analyze(base_r, llm_r)


if __name__ == "__main__":
    main()
