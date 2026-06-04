# Spec Fase 5 — Tool Calling con LangGraph

Esta fase conecta la primera tool real (`TavilySearch`) al grafo LangGraph. Hasta ahora el agente responde con un flujo lineal: recibe mensajes, llama al LLM y termina. En esta fase lo convertimos en un agente con capacidad de decidir cuándo usar herramientas.

## Qué estamos haciendo

Vamos a pasar de este flujo:

```text
START -> agent -> END
```

a este flujo:

```text
START -> agent -> tools -> agent -> END
```

Eso significa que el LLM podrá:

1. Leer la pregunta del usuario.
2. Decidir si necesita una tool.
3. Pedir una llamada a Tavily.
4. Recibir el resultado de Tavily.
5. Responder usando esa información.

Esto es el comienzo del patrón ReAct: razonar, actuar con tools, observar resultado y sintetizar.

## Contexto previo

Ya tenemos:

- `config/settings.py`: settings tipados.
- `services/llm_factory.py`: creación de modelos DeepSeek/Groq.
- `agent/state.py`: estado basado en mensajes.
- `agent/prompts.py`: system prompt inicial.
- `agent/graph.py`: grafo mínimo.
- `tools/tavily_search.py`: factory de Tavily Search Tool.

Esta fase NO crea nuevas tools deportivas todavía. Solo conecta Tavily al grafo para validar el mecanismo.

## Resultado esperado

Al terminar esta fase, el agente debe poder:

1. Construir una lista de tools desde `Settings`.
2. Bindear tools al LLM con `llm.bind_tools(tools)`.
3. Detectar si la respuesta del LLM contiene `tool_calls`.
4. Ejecutar tools mediante `ToolNode`.
5. Volver al nodo `agent` con los resultados.
6. Finalizar cuando el LLM responda sin nuevas tool calls.

## Decisión principal

Modificar `agent/graph.py` para aceptar tools y usar `ToolNode`.

Estructura propuesta:

```text
agent/
├── graph.py      # LangGraph con agent/tools loop
├── prompts.py
└── state.py

tools/
├── tavily_search.py
└── registry.py   # opcional para construir lista de tools
```

Para mantenerlo simple, hay dos opciones.

## Opción recomendada

Crear:

```text
tools/registry.py
```

Con:

```python
def create_tools(settings: Settings):
    return [create_tavily_search_tool(settings)]
```

Y en `agent/graph.py`:

```python
tools = create_tools(settings)
llm = create_chat_model(settings).bind_tools(tools)
```

## Por qué separar registry

Porque `agent/graph.py` no debería saber qué tools concretas existen una por una.

Incorrecto:

```python
from tools.tavily_search import create_tavily_search_tool
```

Aceptable para una prueba, pero escala mal.

Correcto:

```python
from tools.registry import create_tools
```

Así el grafo dice:

> dame las tools disponibles

pero no se acopla a Tavily, FBref, Transfermarkt, etc.

Esto mantiene el grafo como orquestador, no como catálogo de integraciones.

## Diseño del grafo

### Estado

Seguimos usando:

```python
class ScoutingState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
```

Todavía no agregamos `player_data` ni `tool_results`. LangGraph ya guarda tool messages dentro de `messages`.

### Nodo agent

El nodo `agent` debe:

1. Inyectar `SystemMessage(SYSTEM_PROMPT)`.
2. Invocar el LLM con tools bindeadas.
3. Devolver el `AIMessage`.

### Nodo tools

Usaremos:

```python
from langgraph.prebuilt import ToolNode
```

`ToolNode(tools)` recibe el último `AIMessage` con tool calls, ejecuta las tools correspondientes y devuelve `ToolMessage` al estado.

### Condición de continuación

Necesitamos una función:

```python
def should_continue(state: ScoutingState):
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END
```

Si el último mensaje del LLM pide tools, vamos a `tools`. Si no, terminamos.

## Flujo completo

```text
START
  ↓
agent
  ↓
¿hay tool_calls?
  ├── sí → tools → agent
  └── no → END
```

Esto permite múltiples vueltas si el modelo necesita más de una tool.

## Por qué no conectamos todo de golpe

No vamos a meter FBref, Transfermarkt y SofaScore ahora porque todavía estamos probando el mecanismo base.

Si falla algo, queremos saber si el problema está en:

- binding de tools,
- condición de continuación,
- ejecución de ToolNode,
- o Tavily.

Si metemos cinco tools a la vez, el debugging se vuelve barro.

## Testing

Los tests unitarios NO deben llamar a Tavily ni al LLM real.

Estrategia:

- Usar fake LLM que devuelva `AIMessage` sin tool calls.
- Usar fake LLM que devuelva `AIMessage` con tool calls.
- Mockear `create_tools`.
- Mockear o reemplazar tools por una tool falsa simple.

Tests mínimos:

- [ ] Si el LLM responde sin `tool_calls`, el grafo termina.
- [ ] Si el LLM responde con `tool_calls`, el grafo enruta a `tools`.
- [ ] `create_tools(settings)` se usa para construir tools.
- [ ] El LLM recibe tools mediante `bind_tools`.
- [ ] No se llama a Tavily real en tests unitarios.
- [ ] El `SYSTEM_PROMPT` sigue inyectándose antes del mensaje humano.

## Riesgos

### 1. Tests frágiles con mensajes LangChain

Los mensajes con tool calls tienen estructura específica. Hay que usar `AIMessage(tool_calls=[...])` correctamente o una fake tool compatible.

### 2. Loops infinitos

Si el fake LLM siempre devuelve tool calls, el grafo puede entrar en loop. Los tests deben controlar respuestas del fake LLM por turno.

### 3. Acoplar agent a Tavily

No queremos que `agent/graph.py` importe cada tool concreta. Para eso está `tools/registry.py`.

## Fuera de alcance

- Retry/fallback automático.
- Cache de resultados Tavily.
- Prompts avanzados de tool usage.
- Evaluación de calidad.
- Tools deportivas estructuradas.
- Streaming.

## Criterios de aceptación

- [ ] Existe `tools/registry.py`.
- [ ] `agent/graph.py` usa `create_tools(settings)`.
- [ ] `agent/graph.py` usa `llm.bind_tools(tools)`.
- [ ] El grafo tiene nodos `agent` y `tools`.
- [ ] El grafo enruta condicionalmente según `tool_calls`.
- [ ] Los tests pasan sin red ni APIs reales.
- [ ] Ruff pasa.

## Commit sugerido

Rama:

```bash
git checkout dev
git pull
git checkout -b feat/tool-calling-graph
```

Commit:

```bash
git commit -m "feat(agent): add tool calling graph loop"
```

## Resumen simple

Hasta ahora el agente solo hablaba.

En esta fase aprende a decidir:

> “Para responder bien, necesito buscar información externa.”

Y cuando lo necesita, llama a una tool, observa el resultado y responde.

Ese es el salto de chatbot a agente.
