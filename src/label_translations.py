"""Translation dictionaries for Spanish LLM-assigned labels → English."""

APPROACH_LABELS: dict[str, str] = {
    "Metaheurística": "Metaheuristic",
    "Exacto": "Exact method",
    "Survey / Teórico / Modelado": "Survey / Theoretical",
    "Heurística constructiva": "Constructive heuristic",
    "Híbrido / Matheurística": "Hybrid / Matheuristic",
    "No especificado": "Unspecified",
    "Aprendizaje / ML": "Machine learning",
    "No relevante": "Not relevant",
}

VARIANT_LABELS: dict[str, str] = {
    "CARP clásico": "Classical CARP",
    "Otra variante": "Other variant",
    "Estocástico / Incierto": "Stochastic / Uncertain",
    "No es CARP (RPP/CPP/otro)": "Non-CARP (RPP/CPP/other)",
    "Dinámico / Time-dependent": "Dynamic / Time-dependent",
    "Periódico (PCARP)": "Periodic (PCARP)",
    "Multi-depósito": "Multi-depot",
    "Prize-collecting / Profitable": "Prize-collecting / Profitable",
    "Con instalaciones intermedias (CLARPIF)": "Intermediate facilities (CLARPIF)",
    "Large-scale": "Large-scale",
    "Min-max / Balanceado": "Min-max / Balanced",
    "Abierto (OCARP)": "Open (OCARP)",
    "Con ventanas de tiempo (CARPTW)": "Time windows (CARPTW)",
    "Multi-objetivo": "Multi-objective",
    "Windy (WARP)": "Windy (WARP)",
    "Split-delivery": "Split delivery",
    "Mixto (MCARP)": "Mixed (MCARP)",
    "Green / Eléctrico": "Green / Electric",
    "No relevante": "Not relevant",
}

META_LABELS: dict[str, str] = {
    "Algoritmo genético": "Genetic algorithm",
    "Programación genética (hiper-heurística)": "Genetic programming (hyper-heuristic)",
    "Algoritmo memético": "Memetic algorithm",
    "Búsqueda tabú": "Tabu search",
    "Algoritmo evolutivo": "Evolutionary algorithm",
    "MAENS (memético)": "MAENS (memetic)",
    "Simheurística": "Simheuristic",
    "Recocido simulado": "Simulated annealing",
    "SAHiD (descomposición jerárquica)": "SAHiD (hierarchical decomp.)",
    "Coevolución cooperativa": "Cooperative co-evolution",
    "Búsqueda local híbrida (HyLS)": "Hybrid local search (HyLS)",
    "Búsqueda local multi-arranque": "Multi-start local search",
    "Evolución diferencial": "Differential evolution",
    "Divide y vencerás con agrupamiento de rutas": "Divide-and-conquer (route grouping)",
    "Red neuronal": "Neural network",
    "Oscilación estratégica": "Strategic oscillation",
    "Búsqueda local con split de Ulusoy": "Local search with Ulusoy split",
    "Invasive Weed Optimization (IWO)": "Invasive weed optimization (IWO)",
    "Búsqueda tabú granular": "Granular tabu search",
    "Algoritmo inmune artificial": "Artificial immune algorithm",
    "Búsqueda local adaptativa": "Adaptive local search",
    "BRKGA (claves aleatorias sesgadas)": "BRKGA (biased random-key)",
    "Randomización sesgada": "Biased randomization",
    "Búsqueda local evolutiva": "Evolutionary local search",
    "Búsqueda tabú reactiva": "Reactive tabu search",
    "Aprendizaje por refuerzo": "Reinforcement learning",
    # already English – kept for completeness
    "ACO": "ACO",
    "ALNS": "ALNS",
    "Iterated local search": "Iterated local search",
    "VND": "VND",
    "VNS": "VNS",
    "GRASP": "GRASP",
    "Artificial Bee Colony (ABC)": "Artificial bee colony (ABC)",
    "Savings (RandSHARP)": "Savings (RandSHARP)",
    "Savings (SHARP)": "Savings (SHARP)",
    "PSO": "PSO",
    "Electromagnetism-like (EM)": "Electromagnetism-like (EM)",
    "EDA": "EDA",
    "Route Distance Grouping": "Route distance grouping",
    "ELS (evolutionary local search)": "ELS (evolutionary local search)",
    "Monte Carlo Tree Search": "Monte Carlo tree search",
    "Scatter search": "Scatter search",
    "MAENS": "MAENS",
    "MOEA/D": "MOEA/D",
    "NSGA-II": "NSGA-II",
    "Late acceptance hill-climbing": "Late acceptance hill-climbing",
    "Whale Optimization Algorithm": "Whale optimization algorithm",
    "Cuckoo search": "Cuckoo search",
    "Chemical Reaction Optimization (CRO)": "Chemical reaction optimization (CRO)",
    "Augment-merge": "Augment-merge",
    "Multiple scenario approach (MSA)": "Multiple scenario approach (MSA)",
    "Lin-Kernighan-Helsgaun (LKH)": "Lin-Kernighan-Helsgaun (LKH)",
    "Random Route Grouping": "Random route grouping",
    "Path scanning": "Path scanning",
    "LNS": "LNS",
}


def tr_approach(val: str | None) -> str:
    return APPROACH_LABELS.get(val or "", val or "")


def tr_variant(val: str | None) -> str:
    return VARIANT_LABELS.get(val or "", val or "")


def tr_meta(val: str | None) -> str:
    return META_LABELS.get(val or "", val or "")
