# Propuesta — Estructura pragmática por módulos LangChain

Esta propuesta define el scaffolding inicial del proyecto usando módulos alineados con LangChain/LangGraph. La prioridad es avanzar rápido sin perder límites claros: agente, tools, modelos, memoria, configuración y puntos de entrada separados.

## Decisión principal

Usaremos una estructura pragmática por responsabilidad técnica, no una arquitectura Clean/Hexagonal completa desde el día uno.

La razón es simple: el proyecto todavía está en fase de descubrimiento. Forzar capas enterprise antes de tener flujo real sería diseñar una catedral antes de saber dónde va la puerta. Primero necesitamos que el agente funcione, mida, falle de forma clara y pueda extenderse.

## En qué consiste

Una estructura pragmática por módulos LangChain organiza el código alrededor de las piezas reales del agente:

| Módulo | Responsabilidad |
|--------|-----------------|
| `config/` | Cargar y validar `.env`, providers, modelos, paths y rate limits. |
| `agent/` | Definir estado, prompts, grafo LangGraph y construcción del agente. |
| `tools/` | Tools LangChain especializadas: Tavily, FBref, Transfermarkt, comparador, reportes. |
| `models/` | Schemas Pydantic del dominio: jugador, reporte, búsqueda, fuentes. |
| `memory/` | Caché, Chroma, persistencia de perfiles y futuras memorias. |
| `services/` | Lógica reusable que no debería vivir dentro de una tool. |
| `cli/` | Entrada por terminal. |
| `api/` | Entrada HTTP con FastAPI. |
| `tests/` | Unitarios e integración por módulo. |

La clave: una tool no debería convertirse en un archivo gigante que scrapea, normaliza, cachea, decide y responde. Las tools son adaptadores para el agente; la lógica reusable vive en servicios o modelos.

## Estructura propuesta

```text
football-scouting-agent/
├── api/
│   ├── __init__.py
│   └── app.py
├── agent/
│   ├── __init__.py
│   ├── graph.py
│   ├── prompts.py
│   └── state.py
├── cli/
│   ├── __init__.py
│   └── main.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── memory/
│   ├── __init__.py
│   └── chroma_store.py
├── models/
│   ├── __init__.py
│   ├── player.py
│   └── report.py
├── services/
│   ├── __init__.py
│   ├── llm_factory.py
│   └── rate_limit.py
├── tools/
│   ├── __init__.py
│   ├── fbref.py
│   ├── player_compare.py
│   ├── player_search.py
│   ├── report_generator.py
│   ├── tavily_search.py
│   └── transfermarkt.py
├── tests/
│   ├── integration/
│   └── unit/
├── docs/
│   ├── implementation-plan.md
│   └── specs/
├── main.py
├── api.py
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

## Rol de cada capa

### `config/`

Centraliza toda la configuración.

Regla: ningún módulo debe leer `os.getenv()` directamente. Todo pasa por `get_settings()`.

Esto evita duplicación y errores silenciosos. Si el modelo configurado no existe, el error aparece al iniciar, no en mitad de una consulta.

### `agent/`

Contiene la pieza LangGraph:

- `state.py`: estado compartido del grafo.
- `prompts.py`: system prompt y templates.
- `graph.py`: nodos, edges y compilación del grafo.

No debe tener scraping ni lógica de negocio pesada. El agente orquesta; no hace todo.

### `tools/`

Cada tool representa una capacidad invocable por el LLM.

Ejemplos:

- `tavily_search.py`: búsqueda web.
- `fbref.py`: estadísticas avanzadas.
- `transfermarkt.py`: perfil, club, valor de mercado.
- `player_search.py`: búsqueda por criterios.
- `report_generator.py`: generación estructurada del informe.

Regla: la tool debe tener schema Pydantic claro y devolver resultados normalizados.

### `models/`

Define contratos de datos.

Ejemplos:

- `PlayerProfile`
- `ScoutingReport`
- `PlayerSearchCriteria`
- `DataSource`

Esto es FUNDAMENTAL. Sin modelos, terminás pasando diccionarios mágicos por todos lados. Eso escala horrible.

### `memory/`

Se encarga de persistencia y caché:

- Chroma.
- TTL de perfiles.
- Serialización de datos.
- Recuperación por jugador/temporada/fuente.

La memoria no decide qué buscar. Solo guarda y recupera.

### `services/`

Para lógica reusable que no pertenece a una tool concreta.

Ejemplos:

- `llm_factory.py`: crear modelo según settings.
- `rate_limit.py`: delays por fuente.
- futuros normalizadores de datos.

Este módulo evita que las tools crezcan como monstruos.

### `cli/` y `api/`

Separan transporte de lógica:

- CLI para desarrollo y pruebas rápidas.
- API para exponer el agente con FastAPI.

Ambos deben usar el mismo grafo. Si CLI y API implementan lógica distinta, estás duplicando comportamiento y sembrando bugs.

## Qué pasa con `main.py` y `api.py`

Como ya existen en raíz, se pueden mantener como wrappers finos:

- `main.py` llama a `cli.main`.
- `api.py` importa `api.app`.

Esto mantiene compatibilidad con comandos simples:

```bash
python main.py
uvicorn api:app --reload
```

Pero la lógica real vive en carpetas dedicadas.

## Tradeoffs

| Opción | Ventaja | Costo |
|--------|---------|-------|
| Módulos LangChain pragmáticos | Rápido, claro, alineado al stack actual. | Menos formal que Clean Architecture. |
| Clean/Hexagonal completa | Límites arquitectónicos muy fuertes. | Demasiada ceremonia para fase inicial. |
| Todo plano en raíz | Muy rápido al inicio. | Se vuelve inmantenible apenas agregás tools. |

Recomendación: usar módulos LangChain pragmáticos ahora, y refactorizar hacia límites más hexagonales solo cuando aparezca dolor real.

## Scaffolding inicial recomendado

Para Fase 0, solo hace falta crear:

```text
config/
├── __init__.py
└── settings.py

tests/unit/
└── test_settings.py
```

No conviene crear todos los archivos vacíos de golpe. Eso da una falsa sensación de avance. Mejor crear carpetas cuando una fase las necesita.

## Criterios de aceptación del scaffolding

- [ ] El proyecto tiene un módulo `config/` real y testeado.
- [ ] `main.py` y `api.py` quedan como wrappers, no como archivos gigantes.
- [ ] Cada nueva tool vive en `tools/<nombre>.py`.
- [ ] Los modelos Pydantic viven en `models/`.
- [ ] No hay imports circulares entre `agent`, `tools`, `services` y `memory`.
- [ ] Los tests siguen la misma organización que el código.

## Próximo paso sugerido

Si esta estructura te parece bien, el próximo trabajo debería ser implementar Fase 0 en la rama:

```bash
feat/settings
```

Commit esperado:

```bash
feat(config): add typed environment settings
```

