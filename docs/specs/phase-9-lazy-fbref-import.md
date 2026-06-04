# Phase 9 — Lazy import de FBref/soccerdata

## Decisión

El módulo `soccerdata` no debe importarse al construir el grafo ni al registrar tools. Debe importarse únicamente cuando se ejecuta la tool `fbref_stats`.

Esto evita logs, carga innecesaria y efectos secundarios cuando el usuario hace preguntas conceptuales o usa otra tool como Tavily.

## Problema actual

Al ejecutar una consulta conceptual:

```bash
python main.py "Explícame en una frase qué evalúa un scout de fútbol"
```

aparecen logs de soccerdata:

```text
No custom team name replacements found...
No custom league dict found...
```

La respuesta conceptual es correcta, pero el producto se ve ruidoso y confuso.

## Causa raíz

`tools/fbref_stats.py` importa `soccerdata` en el nivel superior del archivo:

```python
import soccerdata as sd
```

Cuando `tools.registry` crea la lista de tools, Python importa `tools.fbref_stats`.
Ese import ejecuta la inicialización de `soccerdata`, aunque la tool FBref no se use.

## Qué es lazy import

Un lazy import es importar una dependencia tarde, justo cuando se necesita.

En vez de esto:

```python
import soccerdata as sd


def fbref_stats(...):
    fbref = sd.FBref(...)
```

hacemos esto:

```python
def fbref_stats(...):
    import soccerdata as sd

    fbref = sd.FBref(...)
```

La diferencia es importante:

| Tipo | Cuándo carga soccerdata | Impacto |
|---|---|---|
| Import eager | al importar el módulo | logs y coste aunque no se use FBref |
| Lazy import | al ejecutar `fbref_stats` | solo hay coste cuando se necesita FBref |

## Objetivo

- Las preguntas conceptuales no deben inicializar soccerdata.
- FBref debe seguir funcionando cuando el usuario pide estadísticas.
- Los tests deben seguir cubriendo la integración sin depender de red ni datos reales.

## Alcance

Incluido:

- mover el import de `soccerdata` dentro de la ejecución de `fbref_stats`;
- adaptar tests que hoy monkeypatchean `tools.fbref_stats.sd.FBref`;
- verificar ruta conceptual, Tavily y FBref.

No incluido:

- cambiar LangGraph;
- cambiar registry;
- crear router explícito;
- modificar proveedores LLM;
- eliminar logs internos de soccerdata cuando FBref sí se usa.

## Diseño técnico

### Antes

```text
main.py
  -> build_graph(settings)
    -> create_tools(settings)
      -> import tools.fbref_stats
        -> import soccerdata
          -> logs/config inicial
```

### Después

```text
main.py
  -> build_graph(settings)
    -> create_tools(settings)
      -> import tools.fbref_stats
        -> NO importa soccerdata todavía

Usuario pide estadísticas FBref
  -> fbref_stats(...)
    -> import soccerdata
    -> sd.FBref(...)
```

## Testing esperado

### Test unitario nuevo

Agregar un test que demuestre que crear la tool no importa `soccerdata`.

Idea:

```python
def test_create_fbref_tool_does_not_import_soccerdata(monkeypatch):
    import sys

    sys.modules.pop("soccerdata", None)

    from tools.fbref_stats import create_fbref_stats_tool

    settings = Settings(_env_file=None)
    create_fbref_stats_tool(settings)

    assert "soccerdata" not in sys.modules
```

### Tests existentes a adaptar

Los tests que hacen:

```python
monkeypatch.setattr("tools.fbref_stats.sd.FBref", FakeFBref)
```

deberán cambiar porque `sd` ya no existirá en el módulo.

Nueva estrategia recomendada:

```python
import types
import sys

fake_soccerdata = types.SimpleNamespace(FBref=FakeFBref)
monkeypatch.setitem(sys.modules, "soccerdata", fake_soccerdata)
```

Así testeamos el lazy import correctamente.

## Verificación manual

### Conceptual

```bash
python main.py "Explícame en una frase qué evalúa un scout de fútbol"
```

Esperado:

- no aparecen logs de soccerdata;
- responde directo;
- no usa FBref.

### FBref

```bash
python main.py "Usa FBref para buscar estadísticas standard de Marc Casado en ESP-La Liga temporada 2025-2026. Dime datos confirmados, limitaciones y fuente"
```

Esperado:

- sí puede aparecer logging de soccerdata;
- devuelve datos FBref;
- cita `FBref vía soccerdata`;
- no muestra campos técnicos.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Tests existentes fallan por no existir `sd` global | Cambiar monkeypatch a `sys.modules["soccerdata"]` |
| Import lazy oculta errores hasta runtime | Es aceptable: FBref solo debe fallar cuando se usa FBref |
| `pandas` sigue importado arriba | Aceptable por ahora; no genera los logs problemáticos |
| El registry sigue creando la tool | Correcto; crear la tool no debe inicializar dependencias pesadas |

## Criterio de aceptación

- [ ] `pytest tests/unit/test_fbref_stats_tool.py` pasa.
- [ ] `pytest tests/unit/test_prompts.py tests/unit/test_agent_graph.py tests/unit/test_tools_registry.py` pasa.
- [ ] `ruff check tools tests/unit/test_fbref_stats_tool.py` pasa.
- [ ] `ruff format --check tools tests/unit/test_fbref_stats_tool.py` pasa.
- [ ] Una consulta conceptual no imprime logs de soccerdata.
- [ ] Una consulta FBref sigue funcionando.

## Decisión arquitectónica

Usamos lazy import porque mantiene la arquitectura simple.

No necesitamos todavía un router explícito ni un sistema avanzado de carga dinámica. El problema actual es concreto: una dependencia con efectos secundarios se carga antes de ser necesaria.

Lazy import resuelve ese problema con bajo coste, bajo riesgo y buen aislamiento.
