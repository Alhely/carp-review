"""Clasificación de artículos de CARP a partir de su título + abstract.

Determina, mediante taxonomías de palabras clave:

  1. La(s) variante(s) del CARP tratadas.
  2. Cómo se resolvió: método exacto, heurística constructiva, metaheurística
     (y de qué tipo) o híbrido / matheurística.

Es un clasificador por reglas (regex con límites de palabra): transparente y
reproducible. No usa modelos externos, así que su precisión depende del texto
disponible; cuando no hay abstract usa solo el título.
"""

from __future__ import annotations

import re
from typing import Any

# --------------------------------------------------------------------------- #
# Taxonomía de VARIANTES del CARP.
# Cada entrada: etiqueta -> lista de patrones (se compilan con \b y IGNORECASE,
# salvo los que ya traen mayúsculas significativas).
# --------------------------------------------------------------------------- #
VARIANT_PATTERNS: dict[str, list[str]] = {
    "Periodic (PCARP)": [r"periodic (capacitated )?arc routing", r"\bPCARP\b"],
    "Stochastic": [r"stochastic (capacitated )?arc routing", r"stochastic demand", r"\bSCARP\b"],
    "Uncertain / Fuzzy / Robust": [r"\bfuzzy\b", r"\brobust\b", r"uncertain(ty)?", r"chance[- ]constrain"],
    "Mixed (MCARP)": [r"mixed (capacitated )?arc routing", r"\bMCARP\b"],
    "Multi-depot": [r"multi[- ]?depot", r"multiple depots?"],
    "Multi-objective": [r"multi[- ]?objective", r"bi[- ]?objective", r"pareto"],
    "Min-max / Balanced": [r"min[- ]?max", r"\bbalanc"],
    "Split delivery": [r"split[- ]delivery", r"split[- ]demand"],
    "Time-dependent / Dynamic": [r"time[- ]dependent", r"\bdynamic arc routing", r"\bonline arc routing"],
    "Time windows (CARPTW)": [r"time window", r"\bCARPTW\b"],
    "Windy (WARP)": [r"windy (rural postman|arc routing|postman)", r"\bwindy\b"],
    "Open (OCARP)": [r"open (capacitated )?arc routing", r"\bOCARP\b"],
    "Prize-collecting / Profitable": [r"prize[- ]collecting", r"profitable", r"team orienteering arc"],
    "Large-scale": [r"large[- ]scale"],
    "Intermediate facilities / IF": [r"intermediate facilit", r"\bIF\b(?!\w)", r"multiple trips?", r"replenish"],
    "Green / Electric": [r"\bgreen\b", r"electric vehicle", r"emission", r"\bCO2\b", r"low[- ]carbon"],
    "Node/General routing (GRP)": [r"general routing problem", r"node[, ]* *edge", r"\bGRP\b"],
    "Rural postman (RPP)": [r"rural postman", r"\bRPP\b"],
    "Chinese postman (CPP)": [r"chinese postman", r"\bCPP\b"],
}

# --------------------------------------------------------------------------- #
# Taxonomía de MÉTODOS de solución, agrupados por categoría.
# --------------------------------------------------------------------------- #
EXACT_PATTERNS: dict[str, list[str]] = {
    "Branch-and-cut": [r"branch[- ]and[- ]cut", r"branch[- ]cut"],
    "Branch-and-price": [r"branch[- ]and[- ]price", r"branch[- ]price"],
    "Branch-and-bound": [r"branch[- ]and[- ]bound", r"branch[- ]bound"],
    "Column generation": [r"column generation"],
    "Cutting plane": [r"cutting[- ]plane"],
    "Integer/Linear programming": [r"integer (linear )?program", r"\bMILP\b", r"\bMIP\b",
                                    r"linear program", r"mathematical program", r"\bILP\b"],
    "Dynamic programming": [r"dynamic programming"],
    "Lagrangian": [r"lagrang"],
}

CONSTRUCTIVE_PATTERNS: dict[str, list[str]] = {
    "Path-scanning": [r"path[- ]scanning"],
    "Augment-merge": [r"augment[- ]merge", r"augment[- ]insert"],
    "Construct-strike": [r"construct[- ]strike"],
    "Ulusoy split / route-first": [r"ulusoy", r"route[- ]first", r"split procedure"],
    "Savings": [r"\bsavings? (algorithm|heuristic|based)"],
    "Greedy / Nearest": [r"\bgreedy\b", r"nearest[- ]neighbou?r"],
}

METAHEURISTIC_PATTERNS: dict[str, list[str]] = {
    "Genetic / Evolutionary": [r"genetic algorithm", r"evolutionary algorithm", r"\bGA\b",
                                r"evolutionary computation", r"genetic programming"],
    "Memetic": [r"memetic"],
    "Ant colony (ACO)": [r"ant colony", r"\bACO\b", r"ant system"],
    "Tabu search": [r"tabu search", r"\btabu\b"],
    "Simulated annealing": [r"simulated annealing"],
    "Variable neighborhood search (VNS)": [r"variable neighou?rhood", r"variable neighbou?rhood", r"\bVNS\b", r"\bVND\b"],
    "Particle swarm (PSO)": [r"particle swarm", r"\bPSO\b"],
    "GRASP": [r"\bGRASP\b", r"greedy randomized adaptive"],
    "Iterated local search (ILS)": [r"iterated local search", r"\bILS\b"],
    "Guided local search": [r"guided local search"],
    "Scatter search / Path relinking": [r"scatter search", r"path[- ]relinking"],
    "Estimation of distribution (EDA)": [r"estimation of distribution", r"\bEDA\b"],
    "Bee / ABC": [r"artificial bee colony", r"\bbee colony\b", r"\bABC algorithm\b"],
    "Differential evolution (DE)": [r"differential evolution"],
    "Large neighborhood search (LNS/ALNS)": [r"\bALNS\b", r"\bLNS\b", r"large neighou?rhood", r"large neighbou?rhood"],
    "Hyper-heuristic": [r"hyper[- ]heuristic"],
    "Cooperative / Swarm (other)": [r"firefly", r"cuckoo", r"grey wolf", r"harmony search",
                                     r"water flow", r"immune algorithm", r"bacterial", r"\bABC\b"],
}

HYBRID_PATTERNS = [r"\bhybrid\b", r"matheuristic", r"math[- ]heuristic", r"cooperative",
                   r"\bmemetic\b"]

GENERIC_HEURISTIC = [r"\bheuristic", r"local search", r"neighou?rhood search", r"metaheuristic"]


def _compile(patterns: list[str]) -> list[re.Pattern]:
    compiled = []
    for pat in patterns:
        # Mantener case-sensitive solo para acrónimos en mayúsculas puros.
        flags = 0 if re.fullmatch(r"\\b[A-Z0-9]+\\b", pat) else re.IGNORECASE
        compiled.append(re.compile(pat, flags))
    return compiled


_COMPILED: dict[str, dict[str, list[re.Pattern]]] = {
    "variant": {k: _compile(v) for k, v in VARIANT_PATTERNS.items()},
    "exact": {k: _compile(v) for k, v in EXACT_PATTERNS.items()},
    "constructive": {k: _compile(v) for k, v in CONSTRUCTIVE_PATTERNS.items()},
    "meta": {k: _compile(v) for k, v in METAHEURISTIC_PATTERNS.items()},
}
_COMPILED_HYBRID = _compile(HYBRID_PATTERNS)
_COMPILED_GENERIC = _compile(GENERIC_HEURISTIC)


def _matches(text: str, compiled: list[re.Pattern]) -> bool:
    return any(p.search(text) for p in compiled)


def _labels(text: str, group: str) -> list[str]:
    return [label for label, pats in _COMPILED[group].items() if _matches(text, pats)]


def classify(title: str | None, abstract: str | None) -> dict[str, Any]:
    """Devuelve variantes y método de solución detectados en título + abstract."""
    text = " ".join(filter(None, [title, abstract]))
    if not text.strip():
        return {
            "variants": [],
            "solution_approach": "unspecified",
            "metaheuristics": [],
            "exact_methods": [],
            "constructive_heuristics": [],
            "is_hybrid": False,
        }

    variants = _labels(text, "variant")
    if not variants:
        variants = ["CARP clásico / no especificado"]

    exact = _labels(text, "exact")
    constructive = _labels(text, "constructive")
    meta = _labels(text, "meta")

    hybrid_signal = _matches(text, _COMPILED_HYBRID)
    # Híbrido si: señal explícita, combina exacto+metaheurística (matheurística),
    # o combina dos o más familias de metaheurísticas.
    is_hybrid = bool(
        hybrid_signal
        or (meta and exact)
        or (len(meta) >= 2)
    )

    if is_hybrid and meta:
        approach = "Híbrido / Matheurística"
    elif meta:
        approach = "Metaheurística"
    elif constructive:
        approach = "Heurística (constructiva)"
    elif exact:
        approach = "Exacto"
    elif _matches(text, _COMPILED_GENERIC):
        approach = "Heurística (genérica)"
    else:
        approach = "No especificado"

    return {
        "variants": variants,
        "solution_approach": approach,
        "metaheuristics": meta,
        "exact_methods": exact,
        "constructive_heuristics": constructive,
        "is_hybrid": is_hybrid,
    }


def enrich_record(record: dict[str, Any]) -> dict[str, Any]:
    """Añade los campos de clasificación a un registro existente."""
    result = classify(record.get("title"), record.get("abstract"))
    record["variants"] = "; ".join(result["variants"])
    record["solution_approach"] = result["solution_approach"]
    record["metaheuristics"] = "; ".join(result["metaheuristics"])
    record["exact_methods"] = "; ".join(result["exact_methods"])
    record["constructive_heuristics"] = "; ".join(result["constructive_heuristics"])
    record["is_hybrid"] = result["is_hybrid"]
    return record
