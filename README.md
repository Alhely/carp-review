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
> abstracts que mencionan muchos términos. Para máxima precisión se puede añadir
> una pasada con un LLM.

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
