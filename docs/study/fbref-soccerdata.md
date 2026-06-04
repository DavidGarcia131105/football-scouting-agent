# Estudio — FBref y soccerdata

Este archivo explica qué es FBref, qué es `soccerdata`, cómo se usan juntos y qué tenemos que entender antes de convertirlos en una tool del agente.

## Qué es FBref

FBref es un sitio de estadísticas de fútbol. Publica datos de equipos, jugadores, partidos y temporadas. Para scouting es valioso porque permite mirar rendimiento con más profundidad que una noticia web.

Ejemplos de datos útiles:

- minutos jugados,
- goles,
- asistencias,
- tiros,
- xG/xAG cuando están disponibles,
- pases,
- creación de tiro/gol,
- acciones defensivas,
- posesión,
- tiempo de juego.

## Qué es soccerdata

`soccerdata` es una librería Python que reúne scrapers para varias fuentes de fútbol, incluyendo FBref. En vez de escribir scraping manual, usamos una clase como:

```python
import soccerdata as sd

fbref = sd.FBref(leagues="ESP-La Liga", seasons="2025-2026")
```

Luego pedimos datos:

```python
stats = fbref.read_player_season_stats(stat_type="standard")
```

El resultado es un `pandas.DataFrame`.

## Cómo funciona por dentro a nivel práctico

Conceptualmente:

```text
Tu código -> soccerdata.FBref -> fbref.com -> HTML/tablas -> pandas.DataFrame -> cache local
```

`soccerdata` hace el trabajo incómodo:

1. construye URLs,
2. descarga páginas,
3. parsea tablas,
4. normaliza nombres de columnas,
5. devuelve DataFrames,
6. guarda cache local.

No es una API oficial de FBref. Es scraping empaquetado. Esa diferencia importa.

## Instalación

El proyecto ya incluye:

```text
soccerdata>=1.6.0
```

Según PyPI, versiones actuales de `soccerdata` soportan Python moderno y devuelven DataFrames con columnas e identificadores pensados para análisis.

## Uso básico

```python
import soccerdata as sd

fbref = sd.FBref(
    leagues="ESP-La Liga",
    seasons="2025-2026",
    data_dir="./data/soccerdata",
)

stats = fbref.read_player_season_stats(stat_type="standard")
```

Donde:

- `leagues`: liga o ligas.
- `seasons`: temporada o temporadas.
- `data_dir`: ruta donde cachear datos.
- `stat_type`: tipo de tabla estadística.

## Ligas

`soccerdata` usa IDs de liga. Ejemplos esperados:

```text
ESP-La Liga
ESP-Segunda División
Big 5 European Leagues Combined
```

Antes de asumir nombres, se puede consultar:

```python
sd.FBref.available_leagues()
```

Eso devuelve ligas disponibles para el scraper FBref.

## Temporadas

`soccerdata` acepta varias formas de temporada según la documentación:

```python
"2025-2026"
"2025-26"
2025
[2024, 2025]
```

Para el proyecto conviene estandarizar en `.env`/tool:

```text
YYYY-YYYY
```

Ejemplo:

```text
2025-2026
```

Es más explícito y fácil de entender.

## Tipos de estadísticas de jugador

`read_player_season_stats(stat_type=...)` soporta:

| stat_type | Qué aporta |
|-----------|------------|
| `standard` | Datos básicos: minutos, goles, asistencias, etc. |
| `shooting` | Tiros, goles, xG si está disponible. |
| `passing` | Pases, progresión, creación desde pase. |
| `passing_types` | Tipos de pase. |
| `goal_shot_creation` | Acciones que terminan en tiro/gol. |
| `defense` | Entradas, bloqueos, intercepciones. |
| `possession` | Toques, conducciones, progresiones. |
| `playing_time` | Minutos, titularidades, participación. |
| `misc` | Métricas varias. |
| `keeper` | Porteros. |
| `keeper_adv` | Porteros avanzado. |

No todos los datos están siempre disponibles para todas las ligas/temporadas. El agente debe ser prudente.

## Ejemplo: buscar un jugador

```python
stats = fbref.read_player_season_stats(stat_type="standard")

player_rows = stats[
    stats["player"].str.contains("Lamine Yamal", case=False, na=False)
]
```

Esto es simple, pero tiene problemas:

- puede devolver cero resultados,
- puede devolver varios jugadores,
- puede fallar si la columna no se llama exactamente `player`,
- puede requerir limpiar MultiIndex.

Por eso la tool debe devolver `count` y `results`, no una única respuesta forzada.

## Cache local

La documentación indica que los datos se descargan cuando hace falta y se cachean localmente. Por defecto, soccerdata usa una ruta dentro del home del usuario, pero nosotros queremos controlar eso con:

```env
SOCCERDATA_DIR=./data/soccerdata
```

Ventajas:

- evita descargar lo mismo muchas veces,
- reduce riesgo de rate limiting,
- mejora latencia,
- hace más claro dónde vive la data.

Cuidado: cache no significa datos frescos. Para actualidad, Tavily sigue siendo mejor.

## Rate limiting y responsabilidad

`soccerdata` es scraping. Hay que usarlo con responsabilidad.

Buenas prácticas:

- preferir cache,
- evitar loops agresivos,
- no lanzar scraping masivo en tests,
- separar tests unitarios de tests de integración,
- respetar términos del sitio fuente.

## Cómo debe usarlo nuestro agente

La tool FBref debe servir para preguntas estadísticas:

```text
"Dame estadísticas de shooting de Lamine Yamal"
"Qué datos de passing tiene Nico Paz esta temporada"
"Busca métricas defensivas de un lateral sub-23"
```

No debería usarse para:

```text
"Está lesionado?"
"Hay rumores de fichaje?"
"Qué noticias hay hoy?"
```

Eso es Tavily.

## Diferencia Tavily vs FBref

| Pregunta | Tool correcta |
|----------|---------------|
| Noticias recientes | Tavily |
| Lesión actual | Tavily |
| Rumores de mercado | Tavily |
| Minutos/goles/xG temporada | FBref/soccerdata |
| Pases progresivos | FBref/soccerdata |
| Acciones defensivas | FBref/soccerdata |

La regla mental:

```text
Tavily = contexto web reciente
FBref = rendimiento estadístico estructurado
```

## Riesgos reales

### 1. FBref puede cambiar

Como `soccerdata` scrapea HTML, cambios en FBref pueden romper columnas, tablas o disponibilidad.

### 2. Algunas estadísticas pueden desaparecer

FBref depende de proveedores de datos. Ciertas métricas avanzadas pueden no estar disponibles siempre.

### 3. Los DataFrames pueden ser complejos

Hay que inspeccionar columnas y convertir a dicts limpios antes de entregarlos al LLM.

### 4. Nombre de jugador ambiguo

No hay que asumir que un string identifica un jugador de forma única.

## Patrón de tool recomendado

```python
class FBrefStatsInput(BaseModel):
    player_name: str | None = None
    league: str = "ESP-La Liga"
    season: str = "2025-2026"
    stat_type: str = "standard"
```

La tool:

1. valida `stat_type`,
2. crea `sd.FBref`,
3. lee stats,
4. filtra jugador si corresponde,
5. convierte DataFrame a dict/list,
6. devuelve metadata de fuente.

## Testing correcto

Unit test correcto:

```python
def test_fbref_tool_filters_player(monkeypatch):
    # mock de sd.FBref
    # DataFrame pequeño en memoria
    # no red
```

Unit test incorrecto:

```python
def test_downloads_real_fbref_data():
    # llama internet real
```

Las pruebas con red deben ser integración explícita y manual, no parte del ciclo unitario.

## Referencias oficiales

- soccerdata FBref API: https://soccerdata.readthedocs.io/en/stable/reference/fbref.html
- soccerdata Getting Started: https://soccerdata.readthedocs.io/en/stable/intro.html
- soccerdata PyPI: https://pypi.org/project/soccerdata/
