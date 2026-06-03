# Plan de implementación continua

Este plan baja el spec técnico del agente de scouting a una secuencia incremental de trabajo. La idea es construir una base sólida primero: configuración, modelos, agente mínimo, tools, memoria, reportes y recién después API/observabilidad.

## Principio de trabajo

No vamos a implementar todo de golpe. Cada fase debe dejar el proyecto en un estado ejecutable, testeable y fácil de extender.

| Regla | Decisión |
|-------|----------|
| Arquitectura | Separar `agent`, `tools`, `models`, `memory` y puntos de entrada. |
| Configuración | Todo provider/model/API key sale de `.env`, nunca hardcodeado. |
| LLM por defecto | `deepseek/deepseek-chat`. |
| Razonamiento | `deepseek/deepseek-reasoner` solo para tareas complejas. |
| Fallbacks | Groq con Qwen, Kimi y Llama según disponibilidad. |
| Entrega | Implementar por fases pequeñas con tests antes de expandir. |

## Fase 0 — Configuración base

Objetivo: tener un proyecto configurable y seguro antes de escribir lógica del agente.

### Tareas

- [ ] Completar `.env.example` con las variables reales esperadas.
- [ ] Crear un módulo de settings tipado con `pydantic-settings`.
- [ ] Validar provider/model configurado contra modelos soportados.
- [ ] Cargar claves de API sin exponer secretos en logs.
- [ ] Definir paths de persistencia para Chroma y cache de `soccerdata`.

### Variables esperadas

```env
APP_ENV=development
LOG_LEVEL=INFO

API_HOST=0.0.0.0
API_PORT=8000

LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat

LLM_REASONING_PROVIDER=deepseek
LLM_REASONING_MODEL=deepseek-reasoner

LLM_FALLBACK_1_PROVIDER=groq
LLM_FALLBACK_1_MODEL=qwen/qwen3-32b

LLM_FALLBACK_2_PROVIDER=groq
LLM_FALLBACK_2_MODEL=moonshotai/kimi-k2

LLM_FALLBACK_3_PROVIDER=groq
LLM_FALLBACK_3_MODEL=llama-3.3-70b-versatile

DEEPSEEK_API_KEY=
GROQ_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
TAVILY_API_KEY=

LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=football-scouting-agent

CHROMA_PERSIST_DIRECTORY=./data/chroma
SOCCERDATA_DIR=./data/soccerdata

TRANSFERMARKT_DELAY_SEC=2.0
FBREF_DELAY_SEC=3.0
SOFASCORE_DELAY_SEC=1.5
```

### Criterios de aceptación

- [ ] El proyecto puede leer configuración desde `.env`.
- [ ] Si falta una key requerida para el provider activo, falla con un error claro.
- [ ] `.env.example` documenta la configuración sin secretos.

## Fase 1 — Núcleo del dominio

Objetivo: definir los contratos antes de implementar tools. Primero conceptos, después código.

### Tareas

- [ ] Crear `models/player.py` con `PlayerProfile`.
- [ ] Crear `models/report.py` con `ScoutingReport`.
- [ ] Definir tipos normalizados para posición, liga, recomendación y fuente.
- [ ] Agregar tests unitarios de validación Pydantic.

### Criterios de aceptación

- [ ] Los modelos validan datos mínimos de un jugador.
- [ ] Los reportes no aceptan recomendaciones fuera del vocabulario definido.
- [ ] Las fuentes quedan trazadas en cada perfil.

## Fase 2 — Selector de LLM

Objetivo: poder cambiar modelo y provider desde `.env` sin tocar código.

### Tareas

- [ ] Crear factory de LLM según `LLM_PROVIDER` y `LLM_MODEL`.
- [ ] Soportar DeepSeek y Groq primero.
- [ ] Preparar soporte futuro para OpenAI y Anthropic.
- [ ] Implementar selección de modelo de razonamiento.
- [ ] Implementar fallback ordenado ante errores del provider principal.

### Criterios de aceptación

- [ ] El agente instancia el modelo configurado.
- [ ] Un modelo inválido produce error explicativo.
- [ ] Los fallbacks se evalúan en orden.

## Fase 3 — LangGraph mínimo

Objetivo: tener el loop del agente funcionando antes de sumar scraping complejo.

### Tareas

- [ ] Crear `agent/state.py` con `ScoutingState`.
- [ ] Crear `agent/prompts.py` con el system prompt.
- [ ] Crear `agent/graph.py` con nodos `agent`, `tools` y salida.
- [ ] Agregar una tool dummy o Tavily inicial para probar tool calling.
- [ ] Crear `main.py` como CLI mínima.

### Criterios de aceptación

- [ ] El usuario puede hacer una pregunta desde CLI.
- [ ] El agente puede decidir usar una tool.
- [ ] El grafo termina sin loops infinitos.

## Fase 4 — Tools de datos

Objetivo: construir tools una por una, testeadas y con límites claros.

### Orden recomendado

1. `web_search` con Tavily.
2. `fbref_stats` con `soccerdata`.
3. `transfermarkt_search` con `httpx` + `BeautifulSoup`.
4. `player_search` combinando fuentes.
5. `player_compare`.
6. `sofascore_rating` como integración futura.

### Tareas

- [ ] Cada tool debe tener schema Pydantic propio.
- [ ] Cada tool debe exponer `_run` y, cuando tenga sentido, `_arun`.
- [ ] Agregar timeouts, retries y rate limiting.
- [ ] Normalizar resultados antes de pasarlos al agente.
- [ ] Escribir tests con mocks para evitar scraping real en CI.

### Criterios de aceptación

- [ ] Cada tool puede probarse aislada.
- [ ] Los errores externos no rompen todo el grafo.
- [ ] Las respuestas incluyen fuente y fecha de obtención.

## Fase 5 — Memoria y caché

Objetivo: evitar consultas repetidas y guardar perfiles útiles.

### Tareas

- [ ] Crear `memory/chroma_store.py`.
- [ ] Definir clave de caché: nombre normalizado + temporada + fuente.
- [ ] Implementar TTL de 24 horas.
- [ ] Cachear `PlayerProfile` serializado.
- [ ] Leer caché antes de hacer scraping.

### Criterios de aceptación

- [ ] Una segunda consulta del mismo jugador usa caché cuando está vigente.
- [ ] Los datos vencidos se refrescan.
- [ ] El agente puede explicar qué fuentes usó.

## Fase 6 — Reportes de scouting

Objetivo: transformar datos en análisis, no solo listar estadísticas.

### Tareas

- [ ] Crear `tools/report_generator.py`.
- [ ] Generar `ScoutingReport` estructurado.
- [ ] Incluir fortalezas, debilidades, potencial y recomendación.
- [ ] Mantener salida en español.
- [ ] Dejar PDF como mejora posterior, no como dependencia inicial.

### Criterios de aceptación

- [ ] El informe sigue el formato del spec.
- [ ] Cada afirmación importante tiene datos o fuente asociada.
- [ ] El reporte distingue entre dato confirmado e inferencia del agente.

## Fase 7 — API y CLI

Objetivo: exponer el agente sin acoplar la lógica al transporte.

### Tareas

- [ ] Mantener CLI en `main.py`.
- [ ] Crear `api.py` con FastAPI.
- [ ] Endpoint `POST /query` para consultas libres.
- [ ] Endpoint `POST /reports/player` para informe por jugador.
- [ ] Endpoint `GET /health` para verificación básica.

### Criterios de aceptación

- [ ] CLI y API usan el mismo grafo.
- [ ] La API no contiene lógica de scouting.
- [ ] Los errores devuelven mensajes claros y no filtran secrets.

## Fase 8 — Observabilidad y evaluación

Objetivo: poder depurar decisiones del agente y medir calidad.

### Tareas

- [ ] Activar LangSmith cuando `LANGSMITH_TRACING=true`.
- [ ] Registrar latencia por tool.
- [ ] Registrar cantidad de iteraciones ReAct.
- [ ] Medir cache hit rate.
- [ ] Crear dataset mínimo de evaluación con consultas esperadas.

### Criterios de aceptación

- [ ] Se puede ver una traza completa de una consulta.
- [ ] Se detectan tools lentas o fallidas.
- [ ] Existe una forma básica de comparar reportes generados contra ejemplos.

## Secuencia recomendada de implementación

```text
Fase 0 → Fase 1 → Fase 2 → Fase 3
                     ↓
        Fase 4 → Fase 5 → Fase 6
                     ↓
              Fase 7 → Fase 8
```

## Primer incremento útil

El primer corte realmente valioso debería permitir:

1. Configurar `deepseek-chat` desde `.env`.
2. Hacer una consulta por CLI.
3. Usar Tavily para obtener contexto web.
4. Devolver una respuesta de scouting básica en español.
5. Registrar la ejecución en LangSmith si está habilitado.

Ese corte evita la trampa de arrancar por scraping complejo. Primero hacemos que el agente respire; después le damos herramientas más potentes.

