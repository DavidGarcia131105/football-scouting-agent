# Spec Fase 2 — LLM Factory

Esta fase define cómo el proyecto convierte configuración tipada en modelos LangChain reales. El objetivo es que el agente pueda seleccionar provider y modelo desde `.env` sin hardcodear DeepSeek, Groq u otros proveedores dentro del grafo.

## Resultado esperado

Al terminar esta fase, el proyecto debe poder:

1. Crear un chat model principal desde `Settings`.
2. Crear un modelo de razonamiento opcional.
3. Preparar modelos fallback configurados.
4. Mantener `agent/` desacoplado de proveedores concretos.
5. Probar la selección de modelos sin llamar APIs reales.

## Decisión principal

Crear un módulo:

```text
services/
├── __init__.py
└── llm_factory.py
```

`config/` valida configuración. `services/llm_factory.py` construye modelos LangChain. `agent/` consume modelos ya construidos.

Esta separación importa: si el grafo empieza a decidir proveedores, modelos, keys y fallback, el agente se convierte en una bola de barro. El grafo debe orquestar comportamiento, no conocer detalles de infraestructura.

## Diseño de responsabilidades

| Módulo | Responsabilidad |
|--------|-----------------|
| `config/settings.py` | Leer `.env` y validar coherencia. |
| `services/llm_factory.py` | Convertir settings en instancias LangChain. |
| `agent/graph.py` | Usar modelos ya creados para ejecutar el flujo. |
| `tests/unit/test_llm_factory.py` | Verificar selección sin llamadas externas. |

## Contrato propuesto

`services/llm_factory.py` debe exponer:

```python
def create_chat_model(settings: Settings) -> BaseChatModel:
    ...


def create_reasoning_model(settings: Settings) -> BaseChatModel:
    ...


def create_fallback_models(settings: Settings) -> list[BaseChatModel]:
    ...
```

Más adelante, si necesitamos más contexto, puede aparecer un objeto:

```python
class LLMBundle(BaseModel):
    primary: BaseChatModel
    reasoning: BaseChatModel | None
    fallbacks: list[BaseChatModel]
```

Pero para esta fase conviene mantenerlo simple. YAGNI: no diseñes una central nuclear para encender una bombilla.

## Providers iniciales

| Provider | Clase LangChain esperada | Paquete |
|----------|--------------------------|---------|
| `deepseek` | `ChatDeepSeek` | `langchain-deepseek` |
| `groq` | `ChatGroq` | `langchain-groq` |

OpenAI y Anthropic quedan fuera de implementación inicial aunque sus keys existan en settings. Están reservados para una fase posterior.

## Nota sobre `init_chat_model`

LangChain expone `init_chat_model()` para inicializar modelos por nombre y provider. Es una abstracción útil, pero la documentación oficial la marca como API beta, por lo que puede cambiar.

Para esta fase se decide NO usar `init_chat_model()` inicialmente. Preferimos instanciar clases concretas (`ChatDeepSeek`, `ChatGroq`) dentro de `services/llm_factory.py`.

Motivos:

- Mantener control explícito sobre provider, modelo y API key.
- Evitar depender de una API beta para la base del proyecto.
- Facilitar tests unitarios verificando clases concretas.
- Reducir comportamiento implícito mientras el agente todavía está naciendo.

Si más adelante `init_chat_model()` se estabiliza o aporta una ventaja clara, puede evaluarse como refactor del factory, no como decisión inicial.

## Configuración esperada

El factory debe consumir estos campos de `Settings`:

```text
llm_provider
llm_model
llm_reasoning_provider
llm_reasoning_model
llm_fallback_1_provider
llm_fallback_1_model
llm_fallback_2_provider
llm_fallback_2_model
llm_fallback_3_provider
llm_fallback_3_model
deepseek_api_key
groq_api_key
```

Si algún campo todavía no existe en `Settings`, esta fase debe extender `config/settings.py` con tests primero.

## Reglas de construcción

### Modelo principal

Si:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
```

Entonces:

```python
create_chat_model(settings)
```

debe crear un `ChatDeepSeek` configurado con:

- modelo `deepseek-chat`
- `DEEPSEEK_API_KEY`
- temperatura default `0`

### Modelo de razonamiento

El modelo de razonamiento debe construirse separado del modelo principal.

Motivo: no todas las tareas necesitan razonamiento paso a paso. Usar `deepseek-reasoner` para todo es gastar capacidad donde no hace falta.

### Fallbacks

Los fallbacks deben prepararse en orden:

1. `groq/qwen/qwen3-32b`
2. `groq/moonshotai/kimi-k2`
3. `groq/llama-3.3-70b-versatile`

Pero esta fase NO ejecuta fallback automático. Solo prepara la lista de modelos disponibles.

La política de fallback real pertenece a una fase posterior, cuando exista el agente/grafo y podamos decidir cómo reintentar sin duplicar efectos de tools.

## Manejo de errores

Errores esperados:

- Provider no soportado por el factory.
- Key requerida ausente para el modelo que se intenta crear.
- Modelo fallback incompleto.

Los errores no deben incluir secretos.

Ejemplo correcto:

```text
Missing API key for provider: GROQ_API_KEY
```

Ejemplo incorrecto:

```text
Invalid key gsk_xxxxx
```

## Testing

Los tests unitarios NO deben llamar APIs reales.

Estrategia recomendada:

- Crear `Settings(_env_file=None)` con `monkeypatch`.
- Verificar que el factory elige la clase correcta.
- Verificar que el modelo configurado queda asignado.
- Verificar que provider no soportado falla.
- Verificar que fallback sin key no se instancia o se ignora según contrato.

Tests mínimos:

- [ ] Crea `ChatDeepSeek` para `deepseek/deepseek-chat`.
- [ ] Crea `ChatGroq` para `groq/qwen/qwen3-32b`.
- [ ] Crea modelo de razonamiento separado.
- [ ] Devuelve fallbacks en orden.
- [ ] No instancia fallback sin key disponible.
- [ ] No expone secrets en errores.

## Decisiones importantes

### No leer `.env` en el factory

El factory recibe `Settings`.

Incorrecto:

```python
api_key = os.getenv("DEEPSEEK_API_KEY")
```

Correcto:

```python
api_key = settings.deepseek_api_key
```

Si cada módulo lee env vars por su cuenta, perdemos control. La configuración tiene que tener una sola puerta de entrada.

### No acoplar LangGraph a providers

`agent/graph.py` no debe contener:

```python
if settings.llm_provider == "deepseek":
    ...
```

Eso pertenece al factory.

### No resolver fallback automático todavía

Parece tentador meter retry/fallback ya, pero todavía no hay grafo ni tools. Si lo hacemos ahora, vamos a inventar comportamiento sin contexto.

Primero construimos modelos. Después diseñamos política de ejecución.

## Tradeoffs

| Enfoque | Ventaja | Costo |
|---------|---------|-------|
| Factory simple por funciones | Fácil de testear y entender. | Puede crecer si sumamos muchos providers. |
| Clase `LLMFactory` | Mejor si hay estado/config compleja. | Más ceremonia ahora. |
| Crear modelos directo en `agent/graph.py` | Rápido al principio. | Acopla grafo a infraestructura. |

Recomendación: empezar con funciones puras en `services/llm_factory.py`. Si el factory crece, recién ahí extraemos clase.

## Criterios de aceptación

- [ ] Existe `services/llm_factory.py`.
- [ ] El factory recibe `Settings`, no lee `.env` directamente.
- [ ] DeepSeek y Groq están soportados.
- [ ] OpenAI y Anthropic no se implementan todavía.
- [ ] Los tests no hacen llamadas reales a proveedores.
- [ ] Los errores no muestran secrets.
- [ ] `agent/` queda libre de lógica de selección de provider.

## Rama y commit sugeridos

Rama:

```bash
git checkout dev
git pull
git checkout -b feat/llm-factory
```

Commit esperado:

```bash
git commit -m "feat(llm): add configurable chat model factory"
```

## Siguiente paso

Después de aprobar esta spec, el siguiente trabajo debe ser TDD:

1. Escribir `tests/unit/test_llm_factory.py`.
2. Verlo fallar porque no existe `services/llm_factory.py`.
3. Implementar lo mínimo para pasar.
4. Recién después conectar el factory con `agent/`.
