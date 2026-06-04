# Estudio — Tavily Search Tool

Este archivo explica qué es Tavily, cómo se usa con LangChain y por qué lo incorporamos como primera tool real del agente de scouting.

## Qué es Tavily

Tavily es una API de búsqueda web pensada para aplicaciones con LLMs y agentes. Sirve para traer contexto reciente o externo cuando el modelo no debería responder solo con conocimiento interno.

En nuestro agente de scouting, Tavily sirve para preguntas como:

- Noticias recientes de un jugador.
- Lesiones o rumores de mercado.
- Contexto general de clubes, convocatorias o rendimiento reciente.
- Fuentes web cuando todavía no tenemos una tool específica.

No reemplaza fuentes deportivas estructuradas como FBref o Transfermarkt. Tavily es búsqueda web general; las estadísticas profundas vendrán de tools especializadas.

## Paquetes disponibles

Hay tres caminos posibles:

| Camino | Uso | Decisión |
|--------|-----|----------|
| `tavily-python` | SDK directo de Tavily. | Útil si queremos cliente propio. |
| `langchain_community.tools.TavilySearchResults` | Integración antigua LangChain. | No usar: deprecated según Tavily. |
| `langchain-tavily` / `TavilySearch` | Integración oficial actual para LangChain. | Usar en este proyecto. |

La decisión para este proyecto es usar `langchain-tavily` porque encaja mejor con tools LangChain y evita arrancar con una integración deprecated.

## Instalación

```bash
pip install -U langchain-tavily
```

En el proyecto se agregará a `requirements.txt`:

```text
langchain-tavily
```

La API key se configura en `.env`:

```env
TAVILY_API_KEY=tvly-...
```

## Sintaxis básica con LangChain

Ejemplo conceptual:

```python
from langchain_tavily import TavilySearch

search_tool = TavilySearch(
    max_results=5,
    topic="general",
    search_depth="basic",
)

result = search_tool.invoke({"query": "Lamine Yamal últimas noticias"})
```

La tool acepta una query natural. En uso con agentes, el LLM decide cuándo invocarla según la descripción de la tool y el contexto del usuario.

## Parámetros principales

| Parámetro | Tipo | Uso |
|-----------|------|-----|
| `max_results` | `int` | Cantidad máxima de resultados. |
| `topic` | `str` | Categoría: `general`, `news` o `finance`. |
| `search_depth` | `str` | Profundidad: `basic` o `advanced`. |
| `include_answer` | `bool` | Incluye respuesta generada por Tavily. |
| `include_raw_content` | `bool` | Incluye contenido HTML limpio/parseado. |
| `include_images` | `bool` | Incluye imágenes relacionadas. |
| `include_domains` | `list[str]` | Limita búsqueda a dominios concretos. |
| `exclude_domains` | `list[str]` | Excluye dominios concretos. |
| `time_range` | `str | None` | Filtra por rango temporal: día, semana, mes o año. |

## Config inicial recomendada

```python
TavilySearch(
    max_results=5,
    topic="general",
    search_depth="basic",
    include_answer=False,
    include_raw_content=False,
    include_images=False,
)
```

Por qué:

- Queremos respuestas pequeñas y controlables.
- Todavía no tenemos estrategia de truncado de raw content.
- El agente debe sintetizar usando fuentes, no delegar la respuesta final a Tavily.
- `basic` reduce coste y latencia mientras validamos el flujo.

## Cuándo debería usarla el agente

Usar Tavily para:

- Información reciente.
- Noticias.
- Contexto no estructurado.
- Verificar afirmaciones temporales.
- Buscar fuentes cuando no hay tool específica.

No usar Tavily para:

- Estadísticas avanzadas si existe FBref/soccerdata.
- Valor de mercado si existe Transfermarkt.
- Ratings partido a partido si existe SofaScore.
- Consultas que el sistema pueda resolver desde memoria/caché local.

## Ejemplos de queries útiles

```text
"Lamine Yamal lesión última hora"
"delanteros sub-21 LaLiga2 goles temporada actual"
"Nico Paz rendimiento Como noticias recientes"
"Real Zaragoza cantera promesas 2026"
```

## Riesgos y límites

### 1. Resultados web no siempre son verdad

Tavily devuelve fuentes web. El agente debe citar o mencionar fuentes cuando use información externa, y debe distinguir dato confirmado de inferencia.

### 2. Puede traer ruido

Una búsqueda amplia puede traer blogs, rumores o contenido repetido. Más adelante convendrá usar `include_domains` y `exclude_domains` para priorizar fuentes fiables.

### 3. Raw content puede inflar tokens

`include_raw_content=True` puede devolver mucho texto. No se activa hasta tener truncado y selección de contexto.

### 4. News requiere intención clara

`topic="news"` es útil para actualidad, pero no todo scouting es noticia. Por defecto usamos `general`.

## Patrón de implementación esperado

```python
from langchain_tavily import TavilySearch

from config.settings import Settings


def create_tavily_search_tool(settings: Settings) -> TavilySearch:
    if not settings.tavily_api_key:
        raise ValueError("Missing API key for Tavily search: TAVILY_API_KEY")

    return TavilySearch(
        api_key=settings.tavily_api_key,
        max_results=5,
        topic="general",
        search_depth="basic",
        include_answer=False,
        include_raw_content=False,
        include_images=False,
    )
```

El punto importante es que la función recibe `Settings`. No lee `.env` directamente.

## Testing esperado

Los tests deben comprobar construcción, no búsqueda real.

Correcto:

```python
def test_creates_tavily_search_tool(monkeypatch):
    ...
```

Incorrecto:

```python
def test_searches_google_live():
    ...
```

Un test unitario con red es frágil, lento y caro. Las llamadas reales pertenecen a tests de integración explícitos.

## Referencias oficiales

- Tavily + LangChain: https://docs.tavily.com/documentation/integrations/langchain
- Tavily Python SDK reference: https://docs.tavily.com/sdk/python/reference
