# Spec Fase 4 — Tavily Search Tool

Esta fase agrega la primera tool real del agente: búsqueda web con Tavily. El objetivo es validar tool calling con una integración externa simple antes de entrar en scraping pesado como Transfermarkt, FBref o SofaScore.

## Contexto previo

Ya tenemos:

- `config/settings.py`: settings tipados y validación de API keys.
- `services/llm_factory.py`: factory de modelos LangChain.
- `agent/graph.py`: LangGraph mínimo con `SYSTEM_PROMPT`.
- Arquitectura pragmática por módulos LangChain.

Esta fase debe respetar el límite arquitectónico: `agent/` orquesta, `tools/` define capacidades, `config/` valida settings y ningún módulo lee `.env` directamente.

## Decisión principal

Usaremos `langchain-tavily` y la clase `TavilySearch` como integración inicial.

La documentación oficial de Tavily recomienda migrar desde `langchain_community.tools.tavily_search.tool` hacia el paquete nuevo `langchain-tavily`, porque la integración antigua está deprecated. Por eso esta fase NO debe usar `TavilySearchResults` de `langchain-community`.

## Resultado esperado

Al terminar esta fase, el proyecto debe poder:

1. Construir una tool de búsqueda web usando `TAVILY_API_KEY` desde `Settings`.
2. Exponer la tool desde `tools/tavily_search.py`.
3. Probar la construcción de la tool sin llamar a la API real.
4. Preparar el camino para conectar tools al grafo en una fase posterior.

## Alcance

### Incluido

- Agregar dependencia `langchain-tavily`.
- Extender validación de settings si hace falta para `TAVILY_API_KEY`.
- Crear `tools/tavily_search.py`.
- Crear factory/helper de tool: `create_tavily_search_tool(settings)`.
- Tests unitarios sin llamadas externas.
- Documentar uso, sintaxis y parámetros en `docs/study/tavily-search-tool.md`.

### Fuera de alcance

- Conectar la tool al grafo LangGraph.
- `llm.bind_tools(...)`.
- `ToolNode`.
- ReAct loop.
- Scraping de fuentes deportivas.
- Caché de resultados.
- Evaluación de calidad de respuestas.

## Dependencia

Actualmente el proyecto tiene:

```text
tavily-python>=0.3.0
langchain-community>=0.3.0
```

Para esta tool LangChain se debe agregar:

```text
langchain-tavily
```

`langchain-community` puede seguir existiendo por otras integraciones, pero no debe usarse para Tavily Search en esta fase.

## Diseño propuesto

Crear:

```text
tools/
└── tavily_search.py
```

Con este contrato:

```python
def create_tavily_search_tool(settings: Settings) -> TavilySearch:
    ...
```

La función debe:

1. Recibir `Settings`.
2. Validar que exista `settings.tavily_api_key`.
3. Crear `TavilySearch` con parámetros seguros por defecto.
4. No ejecutar ninguna búsqueda durante la construcción.

## Configuración recomendada

Valores iniciales:

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

Motivos:

- `max_results=5`: suficiente para contexto inicial sin inflar tokens.
- `topic="general"`: scouting necesita web general al principio; `news` se reserva para consultas explícitamente recientes.
- `search_depth="basic"`: menor coste y latencia inicial.
- `include_answer=False`: preferimos que el agente sintetice usando fuentes, no copiar una respuesta generada por Tavily.
- `include_raw_content=False`: evita contextos enormes hasta tener estrategia de truncado.
- `include_images=False`: fuera de alcance para scouting textual inicial.

## Uso esperado dentro del agente

En una fase posterior, el grafo podrá construir una lista de tools:

```python
tools = [
    create_tavily_search_tool(settings),
]
```

Luego el LLM podrá bindearlas:

```python
llm_with_tools = llm.bind_tools(tools)
```

Pero esta fase no debe hacerlo todavía. Primero construimos y testeamos la tool aislada.

## Reglas de arquitectura

### Permitido

- `tools/tavily_search.py` puede importar `TavilySearch`.
- `tools/tavily_search.py` puede recibir `Settings`.
- Tests pueden mockear la clase `TavilySearch`.

### Prohibido

- Leer `os.getenv("TAVILY_API_KEY")` en `tools/`.
- Usar `TavilySearchResults` de `langchain_community`.
- Hacer llamadas reales a Tavily en tests unitarios.
- Conectar esta tool al grafo sin una fase/spec explícita.

## Manejo de errores

Si falta `TAVILY_API_KEY`, debe fallar con un error claro:

```text
Missing API key for Tavily search: TAVILY_API_KEY
```

El error no debe mostrar secretos.

## Testing

Tests mínimos:

- [ ] `create_tavily_search_tool(settings)` crea una tool Tavily.
- [ ] La tool se crea con `max_results=5`.
- [ ] La tool se crea con `topic="general"`.
- [ ] Si falta `TAVILY_API_KEY`, falla con error claro.
- [ ] El test no llama a la API real.
- [ ] No se importa `TavilySearchResults` desde `langchain_community`.

## Criterios de aceptación

- [ ] Existe `tools/tavily_search.py`.
- [ ] Existe `tests/unit/test_tavily_search_tool.py`.
- [ ] Existe `docs/study/tavily-search-tool.md`.
- [ ] `requirements.txt` incluye `langchain-tavily`.
- [ ] La tool recibe `Settings`, no lee `.env`.
- [ ] Tests unitarios pasan sin red.
- [ ] Ruff pasa.

## Rama y commit sugeridos

Rama:

```bash
git checkout dev
git pull
git checkout -b feat/tavily-search-tool
```

Commit esperado:

```bash
git commit -m "feat(tools): add Tavily search tool"
```

## Referencias oficiales

- Tavily + LangChain: https://docs.tavily.com/documentation/integrations/langchain
- Tavily Python SDK reference: https://docs.tavily.com/sdk/python/reference
