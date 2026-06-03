# Spec Fase 0 — Configuración base

La Fase 0 establece la base de configuración del agente de scouting. El objetivo es que el proyecto pueda leer `.env`, validar providers/modelos, proteger secretos y preparar rutas de persistencia antes de implementar LangGraph o tools reales.

## Resultado esperado

Al terminar esta fase, el proyecto debe poder:

1. Cargar configuración desde `.env`.
2. Validar el provider/modelo activo.
3. Detectar keys requeridas según el provider elegido.
4. Exponer settings tipados para el resto del sistema.
5. Fallar con mensajes claros cuando la configuración sea inválida.

## Alcance

### Incluido

- Settings tipados con `pydantic-settings`.
- `.env.example` completo y seguro.
- Validación de providers soportados.
- Validación de modelos soportados por provider.
- Validación de API keys requeridas.
- Configuración de LangSmith, Chroma, SoccerData y rate limits.
- Tests unitarios de configuración.

### Fuera de alcance

- Instanciar clientes LLM reales.
- Construir LangGraph.
- Implementar tools.
- Ejecutar scraping.
- Implementar memoria Chroma.
- Crear API FastAPI funcional.

## Decisiones de configuración

| Área | Decisión |
|------|----------|
| Archivo fuente | `.env` |
| Ejemplo versionado | `.env.example` |
| Librería | `pydantic-settings` |
| Provider default | `deepseek` |
| Modelo default | `deepseek-chat` |
| Modelo razonamiento | `deepseek-reasoner` |
| Fallbacks | Groq: Qwen, Kimi, Llama |
| Secrets | Nunca loguear valores de keys |

## Variables requeridas

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

## Providers y modelos soportados

| Provider | Modelos |
|----------|---------|
| `deepseek` | `deepseek-chat`, `deepseek-reasoner` |
| `groq` | `qwen/qwen3-32b`, `moonshotai/kimi-k2`, `llama-3.3-70b-versatile` |
| `openai` | reservado para soporte futuro |
| `anthropic` | reservado para soporte futuro |

## Diseño propuesto

Crear un módulo de configuración dedicado:

```text
config/
├── __init__.py
└── settings.py
```

`settings.py` debe exponer:

- `Settings`
- `LLMProvider`
- `SupportedModel`
- `get_settings()`

El resto del proyecto debe consumir configuración desde `get_settings()`, no leyendo `os.getenv()` directamente. Esto es importante: si cada módulo lee env vars por su cuenta, la arquitectura se vuelve una obra sin planos.

## Reglas de validación

### Provider principal

- `LLM_PROVIDER` debe existir en providers soportados.
- `LLM_MODEL` debe pertenecer al provider elegido.
- Si el provider activo requiere key, la key correspondiente debe existir.

Ejemplo:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=
```

Debe fallar porque falta `DEEPSEEK_API_KEY`.

### Modelo de razonamiento

- `LLM_REASONING_PROVIDER` debe ser soportado.
- `LLM_REASONING_MODEL` debe pertenecer a ese provider.
- Su API key debe existir solo si el modelo de razonamiento será usado por configuración futura.

Para Fase 0 se valida compatibilidad provider/modelo, pero no se fuerza su key si el provider principal ya tiene key. Esto evita bloquear el arranque por una capacidad opcional.

### Fallbacks

- Cada fallback debe tener provider y modelo.
- El modelo debe pertenecer al provider.
- Si falta la key del provider de fallback, no debe romper el arranque.
- Debe quedar detectable para que la Fase 2 pueda ignorar fallbacks no disponibles.

## Manejo de errores

Los errores deben ser explícitos:

- `Unsupported provider: <provider>`
- `Unsupported model '<model>' for provider '<provider>'`
- `Missing API key for active provider: <ENV_VAR>`
- `Invalid rate limit value: must be greater than 0`

No deben mostrar valores secretos.

## Tests mínimos

Crear tests para:

- [ ] Carga de defaults.
- [ ] Provider `deepseek` válido.
- [ ] Modelo inválido para provider.
- [ ] Provider inexistente.
- [ ] Falta de key del provider activo.
- [ ] Fallback válido sin key no rompe configuración.
- [ ] Rate limits negativos fallan.
- [ ] Paths de Chroma y SoccerData se cargan correctamente.

## Criterios de aceptación

- [ ] `.env.example` existe y documenta todas las variables.
- [ ] `Settings` puede cargarse desde variables de entorno.
- [ ] La configuración activa falla rápido si es inválida.
- [ ] Ningún secreto aparece en mensajes de error.
- [ ] Los tests de configuración pasan.
- [ ] No hay llamadas directas a `os.getenv()` fuera del módulo de settings.

## Primer commit sugerido para esta fase

```bash
git checkout dev
git pull
git checkout -b feat/settings
```

Commit esperado:

```bash
git commit -m "feat(config): add typed environment settings"
```

## Siguiente fase

Después de esta spec, la Fase 1 puede usar `get_settings()` para construir el selector de LLM sin duplicar lectura de variables.

