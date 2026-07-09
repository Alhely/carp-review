"""Prepara los abstracts para clasificación LLM local (dentro de Claude Code).

Genera data/llm_input.jsonl: una línea compacta por artículo con abstract,
{"i": idx, "t": título, "a": abstract truncado}. El índice `i` es la posición
dentro de la lista de artículos-con-abstract y sirve para fusionar después.
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ABSTRACT_MAXLEN = 800  # suficiente para determinar variante y método


def main() -> None:
    records = json.loads((DATA_DIR / "carp_articles.json").read_text(encoding="utf-8"))
    with_abs = [r for r in records if r.get("abstract")]

    out = DATA_DIR / "llm_input.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for i, r in enumerate(with_abs):
            abstract = (r["abstract"] or "")[:ABSTRACT_MAXLEN]
            line = {"i": i, "t": r.get("title") or "", "a": abstract}
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")

    print(f"{len(with_abs)} artículos con abstract -> {out}")


if __name__ == "__main__":
    main()
