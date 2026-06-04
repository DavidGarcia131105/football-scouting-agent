# Spec Fase 8 — FBref Stats Tool con soccerdata

Esta fase agrega la primera tool deportiva estructurada del agente: estadísticas de jugador desde FBref usando `soccerdata`. Hasta ahora el agente puede buscar contexto web con Tavily, pero eso no alcanza para scouting serio. Necesitamos datos futbolísticos tabulares: minutos, goles, asistencias, xG, pases, defensa, posesión y otros perfiles estadísticos.

## Qué estamos haciendo

Vamos a crear una tool LangChain que permita al agente consultar estadísticas de jugadores desde FBref mediante `soccerdata`.

La tool responderá preguntas del estilo:

```text
"Dame estadísticas de Lamine Yamal en La Liga 2025-2026"
"Busca datos de shooting para delanteros jóvenes en LaLiga"
"Necesito métricas de passing de un mediocentro sub-23"
```

## Por qué esta fase mejora el producto

Tavily trae noticias y contexto web. FBref/soccerdata trae datos estructurados.

Un agente de scouting necesita ambas cosas:

- Tavily: actualidad, lesiones, rumores, contexto.
- FBref/soccerdata: rendimiento cuantificable.

Sin datos estadísticos, el agente puede sonar bien pero no analiza fútbol con rigor.

## Decisión principal

Crear:

```text
tools/
└── fbref_stats.py
```

Con una factory:

```python
def create_fbref_stats_tool(settings: Settings) -> BaseTool:
    ...
```

La tool usará internamente `soccerdata.FBref`.

## Fuente técnica

`soccerdata` expone una clase `FBref` que descarga datos desde `fbref.com` y devuelve `pandas.DataFrame`. Según su documentación, cachea localmente los datos descargados y permite configurar `data_dir`.

La API relevante para esta fase es:

```python
fbref = sd.FBref(leagues=..., seasons=..., data_dir=...)
stats = fbref.read_player_season_stats(stat_type="standard")
```

`read_player_season_stats` permite estos `stat_type`:

- `standard`
- `shooting`
- `passing`
- `passing_types`
- `goal_shot_creation`
- `defense`
- `possession`
- `playing_time`
- `misc`
- `keeper`
- `keeper_adv`

## Alcance

### Incluido

- Crear `tools/fbref_stats.py`.
- Definir schema Pydantic para input de la tool.
- Consultar `soccerdata.FBref.read_player_season_stats`.
- Filtrar por nombre de jugador cuando se provea.
- Soportar liga, temporada y tipo de estadística.
- Usar `SOCCERDATA_DIR` desde `Settings`.
- Tests unitarios con mock de `soccerdata.FBref`, sin scraping real.
- Estudio técnico en `docs/study/fbref-soccerdata.md`.

### Fuera de alcance

- Player search complejo por criterios múltiples.
- Ranking de jugadores.
- Comparador de jugadores.
- Normalización avanzada de nombres.
- Cache propia en Chroma.
- Tests de integración con FBref real.
- Transfermarkt/SofaScore.

## Diseño de input

La tool debe tener un schema parecido a:

```python
class FBrefStatsInput(BaseModel):
    player_name: str | None = Field(default=None, description="Nombre parcial o exacto del jugador")
    league: str = Field(default="ESP-La Liga", description="Liga soccerdata/FBref")
    season: str = Field(default="2025-2026", description="Temporada en formato YYYY-YYYY")
    stat_type: str = Field(default="standard", description="standard|shooting|passing|defense|...")
```

## Diseño de salida

La tool debe devolver una estructura serializable, no un DataFrame crudo.

Formato recomendado:

```python
{
    "source": "fbref",
    "league": "ESP-La Liga",
    "season": "2025-2026",
    "stat_type": "standard",
    "count": 1,
    "results": [...],
}
```

Motivo: los mensajes de tools deben ser fáciles de leer por el LLM y seguros de serializar.

## Configuración

Usar:

```env
SOCCERDATA_DIR=./data/soccerdata
FBREF_DELAY_SEC=3.0
```

`SOCCERDATA_DIR` define dónde `soccerdata` guarda cache local.

`FBREF_DELAY_SEC` queda preparado para rate limiting, aunque en esta fase puede no aplicarse todavía si solo usamos la cache/API de `soccerdata`.

## Validación de `stat_type`

La tool debe validar explícitamente los tipos soportados antes de llamar a FBref.

Si llega:

```text
stat_type="banana"
```

Debe fallar con error claro:

```text
Unsupported FBref stat_type: banana
```

No queremos que el agente reciba un traceback interno de soccerdata.

## Testing

Los tests unitarios NO deben llamar a FBref real.

Estrategia:

- Mockear `soccerdata.FBref`.
- Hacer que `read_player_season_stats` devuelva un `pandas.DataFrame` pequeño.
- Verificar que la tool filtra por `player_name`.
- Verificar que devuelve dict/list serializable.
- Verificar que `stat_type` inválido falla antes de llamar a soccerdata.

Tests mínimos:

- [ ] Crea la tool FBref.
- [ ] Llama a `sd.FBref` con liga, temporada y `data_dir`.
- [ ] Llama a `read_player_season_stats(stat_type=...)`.
- [ ] Filtra por nombre de jugador.
- [ ] Devuelve resultado serializable.
- [ ] Rechaza `stat_type` inválido.
- [ ] No hace scraping real en unit tests.

## Registro de tools

Cuando la tool esté lista, `tools/registry.py` debe incluirla:

```python
def create_tools(settings: Settings):
    return [
        create_tavily_search_tool(settings),
        create_fbref_stats_tool(settings),
    ]
```

Pero si `create_fbref_stats_tool` no necesita API key, no debería bloquear el arranque.

## Riesgos técnicos

### 1. Scraping frágil

`soccerdata` scrapea sitios externos. La propia documentación/paquete advierte que cambios en los sitios pueden romper el paquete. No hay que diseñar como si fuera una API garantizada.

### 2. Cache local

`soccerdata` descarga datos cuando hace falta y los cachea. Esto es bueno para latencia y rate limiting, pero puede devolver datos antiguos si no se entiende la cache.

### 3. MultiIndex y columnas complejas

Los DataFrames de FBref pueden venir con índices/columnas no triviales. La tool debe convertirlos a una estructura simple antes de devolverlos.

### 4. Nombres ambiguos

Filtrar por `str.contains(player_name)` puede traer más de un jugador o falsos positivos. La tool debe devolver `count` y no fingir certeza cuando hay múltiples resultados.

## Criterios de aceptación

- [ ] Existe `tools/fbref_stats.py`.
- [ ] Existe `tests/unit/test_fbref_stats_tool.py`.
- [ ] Existe `docs/study/fbref-soccerdata.md`.
- [ ] La tool usa `Settings`, no lee `.env` directamente.
- [ ] La tool usa `SOCCERDATA_DIR`.
- [ ] Tests unitarios pasan sin red.
- [ ] Ruff pasa.
- [ ] `tools/registry.py` incluye Tavily + FBref.

## Rama y commit sugeridos

Rama:

```bash
git checkout dev
git pull
git checkout -b feat/fbref-stats-tool
```

Commit:

```bash
git commit -m "feat(tools): add FBref stats tool"
```

## Referencias oficiales

- soccerdata FBref API: https://soccerdata.readthedocs.io/en/stable/reference/fbref.html
- soccerdata Getting Started: https://soccerdata.readthedocs.io/en/stable/intro.html
- soccerdata PyPI: https://pypi.org/project/soccerdata/
