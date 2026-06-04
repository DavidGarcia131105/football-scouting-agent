# Spec Fase 3 — LangGraph mínimo

Esta fase conecta la configuración y el LLM factory con un grafo LangGraph mínimo. El objetivo no es construir todavía el agente completo de scouting, sino probar que el motor conversacional arranca con límites claros: estado, prompt, modelo y flujo básico.

## Contexto previo

Ya tenemos:

- `config/settings.py`: carga y valida `.env`.
- `services/llm_factory.py`: crea modelos DeepSeek/Groq desde `Settings`.
- Estructura pragmática por módulos LangChain.
- Decisión arquitectónica: `agent/` orquesta, pero no decide providers ni lee variables de entorno.

Esta fase debe respetar esas decisiones. NO vamos a meter scraping, tools reales ni memoria todavía. Primero el motor. Después los accesorios.

## Resultado esperado

Al terminar esta fase, el proyecto debe poder:

1. Construir un `StateGraph` mínimo.
2. Usar el modelo principal creado por `services/llm_factory.py`.
3. Recibir un mensaje de usuario.
4. Devolver una respuesta del modelo.
5. Mantener `agent/` desacoplado de providers concretos.

## Decisión principal

Crear estos archivos:

```text
agent/
├── state.py
├── prompts.py
└── graph.py
```

Responsabilidades:

| Archivo | Responsabilidad |
|---------|-----------------|
| `agent/state.py` | Definir `ScoutingState`, el contrato del estado del grafo. |
| `agent/prompts.py` | Definir el `SYSTEM_PROMPT` inicial del agente. |
| `agent/graph.py` | Construir y compilar el grafo LangGraph mínimo. |

## Alcance

### Incluido

- Estado mínimo basado en mensajes.
- Prompt inicial de scouting en español.
- Nodo `agent`.
- Grafo `agent -> END`.
- Uso de `create_chat_model(settings)`.
- Tests unitarios sin llamadas reales al LLM.

### Fuera de alcance

- Tools reales.
- Tool calling.
- ReAct loop completo.
- Scraping.
- Chroma/memoria.
- API FastAPI.
- CLI rica.
- Streaming.
- Retry/fallback automático.

## Diseño del estado

Para esta fase, el estado debe ser pequeño:

```python
from typing import Annotated, TypedDict
import operator

from langchain_core.messages import BaseMessage


class ScoutingState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
```

Motivo: todavía no hay `player_data`, `tool_results` ni `report_ready`. Agregar campos sin uso es ruido. Los campos aparecen cuando el flujo los necesita.

## Prompt inicial

`agent/prompts.py` debe exponer:

```python
SYSTEM_PROMPT = """
Eres un asistente experto en scouting de fútbol español especializado en jóvenes talentos U16-U23.
Responde siempre en español, con análisis claro, prudente y basado en datos disponibles.
Si no tienes datos suficientes, dilo explícitamente y explica qué fuente haría falta consultar.
"""
```

Este prompt es deliberadamente pequeño. El prompt complejo con guía de tools pertenece a una fase posterior, cuando las tools existan.

## Diseño del grafo

`agent/graph.py` debe exponer una función:

```python
def build_graph(settings: Settings):
    ...
```

El flujo mínimo:

```text
START -> agent -> END
```

El nodo `agent`:

1. Crea/recibe el LLM desde `create_chat_model(settings)`.
2. Prepara mensajes con `SystemMessage(SYSTEM_PROMPT)`.
3. Invoca el modelo.
4. Devuelve el nuevo mensaje del asistente.

## Regla de dependencia

`agent/graph.py` puede importar:

- `Settings`
- `create_chat_model`
- `SYSTEM_PROMPT`
- `ScoutingState`

Pero NO puede importar:

- `ChatDeepSeek`
- `ChatGroq`
- `os.getenv`

Si `agent/graph.py` conoce providers concretos, rompimos la arquitectura.

## Testing

Los tests de esta fase no deben llamar APIs reales.

Estrategia:

- Mockear `create_chat_model`.
- Usar un fake LLM con método `invoke`.
- Verificar que `build_graph(settings)` devuelve un grafo invocable.
- Verificar que el grafo agrega una respuesta del asistente.
- Verificar que el prompt de sistema se inyecta antes del mensaje humano.

Tests mínimos:

- [ ] `ScoutingState` acepta lista de mensajes.
- [ ] `build_graph(settings)` compila un grafo.
- [ ] El grafo invoca el modelo con `SystemMessage` + mensajes del usuario.
- [ ] El resultado contiene el mensaje del asistente.
- [ ] `agent/graph.py` no instancia providers concretos.

## Manejo de errores

En esta fase no se diseña retry.

Si el LLM falla, el error puede propagarse. Es mejor ver el fallo real durante desarrollo que ocultarlo con lógica prematura.

La estrategia de retry/fallback pertenece a una fase posterior, cuando exista un flujo con tools y podamos decidir qué operaciones son seguras de repetir.

## Tradeoffs

| Enfoque | Ventaja | Costo |
|---------|---------|-------|
| Grafo mínimo `agent -> END` | Fácil de entender y testear. | Todavía no razona con tools. |
| ReAct completo desde ya | Se parece más al producto final. | Demasiadas variables al depurar. |
| Invocar LLM directo sin LangGraph | Más simple inicialmente. | No prueba la arquitectura objetivo. |

Recomendación: usar LangGraph mínimo. Es el punto medio correcto: prueba la arquitectura sin meter complejidad prematura.

## Criterios de aceptación

- [ ] Existe `agent/state.py`.
- [ ] Existe `agent/prompts.py`.
- [ ] Existe `agent/graph.py`.
- [ ] `build_graph(settings)` usa `create_chat_model(settings)`.
- [ ] El grafo se puede invocar con mensajes.
- [ ] Tests unitarios pasan sin llamadas externas.
- [ ] `agent/` no lee `.env`.
- [ ] `agent/` no importa clases concretas de providers.

## Rama y commit sugeridos

Rama:

```bash
git checkout dev
git pull
git checkout -b feat/langgraph-minimal
```

Commit esperado:

```bash
git commit -m "feat(agent): add minimal LangGraph flow"
```

## Siguiente paso

Después de aprobar esta spec:

1. Escribir tests RED para `agent/graph.py`.
2. Implementar `state.py`, `prompts.py` y `graph.py`.
3. Verificar con `pytest` y `ruff`.
4. Recién después pensar en tools.

No saltees esto. CONCEPTOS > CÓDIGO: primero hacemos que el grafo respire; después le damos manos para usar herramientas.

