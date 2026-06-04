# Spec Fase 6 — CLI mínima

Esta fase agrega una entrada por terminal para invocar el grafo del agente con una pregunta del usuario. El objetivo es probar el flujo completo localmente sin construir todavía una API ni una interfaz compleja.

## Qué estamos haciendo

Queremos poder ejecutar:

```bash
python main.py "Busca noticias recientes de Lamine Yamal"
```

Y que el programa:

1. Cargue `Settings` desde `.env`.
2. Construya el grafo con `build_graph(settings)`.
3. Convierta la pregunta en `HumanMessage`.
4. Ejecute el grafo.
5. Imprima la última respuesta del asistente.

## Contexto previo

Ya tenemos:

- Configuración tipada.
- Factory de LLM.
- Tavily Search Tool.
- Grafo LangGraph con loop de tool calling.

La CLI será solo un wrapper. No debe contener lógica de scouting ni lógica de tools.

## Alcance

### Incluido

- Implementar `main.py` como entrada CLI simple.
- Leer pregunta desde argumentos de terminal.
- Invocar el grafo.
- Imprimir respuesta final.
- Tests unitarios sin llamar LLM real.

### Fuera de alcance

- Modo interactivo largo.
- Streaming.
- FastAPI.
- Rich UI avanzada.
- Manejo complejo de historial.
- Guardar conversaciones.

## Diseño propuesto

`main.py` debe exponer:

```python
def run_cli(argv: list[str] | None = None) -> int:
    ...
```

Y usar:

```python
if __name__ == "__main__":
    raise SystemExit(run_cli())
```

Esto permite testear `run_cli()` sin ejecutar el proceso entero.

## Flujo

```text
argv -> pregunta -> Settings -> build_graph -> HumanMessage -> graph.invoke -> print respuesta
```

## Reglas de arquitectura

Permitido:

- `main.py` importa `Settings`.
- `main.py` importa `build_graph`.
- `main.py` crea `HumanMessage`.

Prohibido:

- `main.py` no importa `ChatDeepSeek`, `ChatGroq` ni Tavily.
- `main.py` no lee `os.getenv`.
- `main.py` no decide tools.
- `main.py` no contiene prompt engineering.

## Manejo de errores

Si no hay pregunta:

```text
Usage: python main.py "tu pregunta"
```

Debe devolver código `1`.

Si hay pregunta y el grafo responde, devuelve código `0`.

## Testing

Tests mínimos:

- [ ] Sin argumentos devuelve `1` y muestra usage.
- [ ] Con pregunta invoca `build_graph`.
- [ ] Convierte la pregunta en `HumanMessage`.
- [ ] Imprime el contenido del último `AIMessage`.
- [ ] Tests no llaman LLM real ni Tavily real.

## Criterios de aceptación

- [ ] `main.py` tiene `run_cli()` testeable.
- [ ] `python main.py "pregunta"` funciona.
- [ ] La CLI usa el grafo existente.
- [ ] Tests pasan.
- [ ] Ruff pasa.

## Commit sugerido

Rama:

```bash
git checkout dev
git pull
git checkout -b feat/cli-minimal
```

Commit:

```bash
git commit -m "feat(cli): add minimal graph runner"
```
