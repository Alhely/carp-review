# CARP review

Recolector de literatura científica sobre el **Capacitated Arc Routing Problem
(CARP)**, sus variantes y su metodología.

Consulta la API pública y gratuita de [OpenAlex](https://openalex.org), que
indexa a todas las grandes editoriales científicas (Elsevier/ScienceDirect,
IEEE Xplore, Springer, Wiley, Taylor & Francis, etc.). **No descarga los PDF**:
solo recupera metadatos.

## Datos recuperados por artículo

- `doi`
- `title`
- `abstract`
- `publication_year`
- `venue` — revista o conferencia donde se publicó
- `publisher`
- `is_open_access` — si es o no de libre acceso
- `oa_status` — tipo de acceso (gold / green / hybrid / bronze / closed)
- `work_type`, `cited_by_count`, `openalex_id`

### Clasificación (derivada de título + abstract)

Un clasificador por palabras clave ([`src/classifier.py`](src/classifier.py))
añade, analizando el texto:

- `variants` — variante(s) del CARP (periódico, estocástico, mixto,
  multi-depósito, windy, multi-objetivo, con ventanas de tiempo, etc.)
- `solution_approach` — Exacto / Heurística / Metaheurística / Híbrido-Matheurística
- `metaheuristics` — tipo(s) concretos (GA, memético, ACO, tabú, VNS, ALNS…)
- `exact_methods`, `constructive_heuristics`, `is_hybrid`

Para reclasificar datos ya recolectados sin volver a descargar:

```bash
python src/enrich.py
```

> Es un clasificador por reglas: rápido y reproducible, pero puede sobre-etiquetar
> abstracts que mencionan muchos términos.

### Clasificación semántica con LLM (Claude)

Para máxima precisión, una clasificación con LLM asigna **una** variante y **un**
método principal por artículo (sin sobre-etiquetar) y añade un resumen de cómo se
resolvió. Genera `data/carp_articles_llm.csv` / `.json` con las columnas
`llm_relevance`, `llm_variant`, `llm_approach`, `llm_metaheuristics`,
`llm_is_hybrid`, `llm_how_solved`.

Dos formas de obtenerla:

- **Vía Batch API** ([`src/llm_classifier.py`](src/llm_classifier.py)) — automática
  y barata (Batch API + structured outputs). Requiere `ANTHROPIC_API_KEY`:
  ```bash
  export ANTHROPIC_API_KEY=sk-ant-...
  python src/llm_classifier.py
  ```
- **Local** ([`src/llm_local_prep.py`](src/llm_local_prep.py) +
  [`src/llm_local_merge.py`](src/llm_local_merge.py)) — el prep genera
  `data/llm_input.jsonl`; las clasificaciones se guardan en
  `data/llm_results/*.json` y el merge las une al CSV/JSON final.

## Análisis y gráficos

[`src/analysis.py`](src/analysis.py) genera gráficos en `data/figures/` (por año,
variantes, enfoques, metaheurísticas, open access, evolución de enfoques) y la
tabla cruzada `data/crosstab_variante_enfoque.csv`:

```bash
python src/analysis.py
```

## Uso

```bash
pip install -r requirements.txt
python src/main.py
```

Los resultados se guardan en `data/`:

- `data/carp_articles.csv`
- `data/carp_articles.json`

## Configuración

Edita `SEARCH_PHRASES` en [`src/carp_scraper.py`](src/carp_scraper.py) para
ajustar los términos de búsqueda (variantes y metodología).
