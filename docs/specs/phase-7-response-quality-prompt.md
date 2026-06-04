# Spec Fase 7 — Calidad de respuesta y guía de uso de tools

Esta fase mejora el comportamiento del agente sin agregar nuevas integraciones. Ya tenemos un flujo funcional: CLI, LangGraph, LLM, Tavily y tool calling. Ahora necesitamos que el producto responda con más rigor.

El objetivo es evitar respuestas bonitas pero poco confiables. Un agente de scouting no puede limitarse a sonar convincente: debe distinguir datos, fuentes, incertidumbre e inferencias.

## Qué problema resolvemos

Hoy el agente puede buscar en web y responder, pero todavía no tiene reglas fuertes para:

- citar o mencionar fuentes usadas,
- explicar cuándo está infiriendo,
- reconocer falta de datos,
- evitar sobreafirmaciones,
- estructurar respuestas de scouting de forma consistente,
- usar Tavily solo cuando aporta valor.

Esto es crítico. Si el agente inventa seguridad, no sirve para scouting. En fútbol, un dato mal interpretado puede llevar a una mala recomendación.

## Resultado esperado

Al terminar esta fase, el agente debe responder con una estructura más útil:

1. Resumen breve.
2. Datos encontrados.
3. Fuentes o contexto usado.
4. Inferencias separadas de hechos.
5. Limitaciones o datos faltantes.
6. Próximo paso recomendado.

No todas las respuestas necesitan todos los bloques, pero las consultas de scouting o actualidad sí deben seguir esa lógica.

## Decisión principal

Mejorar `SYSTEM_PROMPT` en:

```text
agent/prompts.py
```

Y mantenerlo testeado.

No vamos a meter lógica compleja en código para formatear respuestas todavía. Primero damos instrucciones claras al agente. Si luego vemos que el prompt no alcanza, evaluamos output parsers o modelos Pydantic.

## Principios de respuesta

### 1. Datos > opiniones

El agente debe priorizar datos concretos:

- edad,
- club,
- posición,
- competición,
- minutos,
- goles/asistencias,
- lesión,
- fuente temporal,
- fecha de actualización.

Si no tiene datos, debe decirlo.

### 2. Fuentes visibles

Cuando use web/Tavily, debe mencionar las fuentes de forma natural.

Ejemplo:

```text
Según resultados recientes de FIFA y prensa deportiva española...
```

No hace falta una bibliografía formal todavía, pero sí indicar de dónde viene la información.

### 3. Separar hecho de inferencia

Incorrecto:

```text
Es una apuesta segura para fichar.
```

Correcto:

```text
Dato confirmado: fue incluido en la convocatoria.
Inferencia: si mantiene minutos y estado físico, su seguimiento prioritario está justificado.
```

### 4. No sobreactuar actualidad

Si la pregunta requiere actualidad, usar Tavily.

Si la pregunta es conceptual, no hace falta buscar.

Ejemplos:

| Pregunta | ¿Usar Tavily? | Motivo |
|----------|---------------|--------|
| “Qué hace un scout?” | No | Conceptual. |
| “Noticias recientes de Lamine Yamal” | Sí | Actualidad. |
| “Compará dos jugadores con datos actuales” | Sí, si no hay tool estadística. | Necesita contexto. |
| “Explicá qué es xG” | No | Conceptual. |

### 5. Ser prudente con scouting

El agente no debe recomendar fichajes de forma absoluta si solo tiene noticias web. Debe hablar de seguimiento, señales, riesgos y datos faltantes.

## Prompt propuesto

`SYSTEM_PROMPT` debería evolucionar hacia:

```text
Eres un asistente experto en scouting de fútbol español especializado en jóvenes talentos U16-U23.

Tu objetivo es ayudar a scouts y analistas a tomar mejores decisiones, no sonar convincente sin evidencia.

Reglas de rigor:
- Responde siempre en español.
- Prioriza datos verificables sobre opiniones.
- Si usas información web o resultados de tools, menciona las fuentes o el contexto usado.
- Distingue claramente entre datos confirmados e inferencias.
- Si faltan datos importantes, dilo explícitamente.
- No inventes estadísticas, lesiones, clubes, edades ni convocatorias.
- Para actualidad, noticias, lesiones o rumores, usa búsqueda web antes de responder.
- Para explicaciones conceptuales, no uses tools salvo que el usuario pida información reciente.

Formato recomendado para scouting o actualidad:
1. Resumen breve
2. Datos encontrados
3. Lectura futbolística
4. Limitaciones / datos faltantes
5. Próximo paso recomendado
```

## Alcance

### Incluido

- Mejorar `SYSTEM_PROMPT`.
- Agregar tests sobre contenido mínimo del prompt.
- Documentar criterios de respuesta.
- Mantener compatibilidad con el grafo actual.

### Fuera de alcance

- Output parser Pydantic.
- Generación PDF.
- Evaluaciones LangSmith.
- Nuevas tools deportivas.
- Cambiar el grafo.
- Forzar formato rígido para todas las respuestas.

## Testing

Los tests deben validar que el prompt contiene reglas importantes.

Tests mínimos:

- [ ] El prompt exige responder en español.
- [ ] El prompt exige no inventar datos.
- [ ] El prompt exige separar datos confirmados de inferencias.
- [ ] El prompt indica usar búsqueda web para actualidad/noticias/lesiones.
- [ ] El grafo sigue inyectando `SYSTEM_PROMPT` antes del mensaje humano.

Esto no prueba que el LLM siempre obedezca. Pero protege que no borremos accidentalmente las reglas del prompt.

## Criterios de aceptación

- [ ] `agent/prompts.py` contiene prompt mejorado.
- [ ] Tests del prompt pasan.
- [ ] Tests del grafo siguen pasando.
- [ ] Ruff pasa.
- [ ] La CLI sigue funcionando.

## Rama y commit sugeridos

Rama:

```bash
git checkout dev
git pull
git checkout -b feat/response-quality-prompt
```

Commit:

```bash
git commit -m "feat(prompt): improve scouting response quality rules"
```

## Por qué esta fase mejora el producto

Porque aumenta confianza.

Un agente que busca información pero no explica qué es dato, qué es inferencia y qué falta, parece útil pero puede ser peligroso. Esta fase hace que el agente sea más honesto, más analítico y más cercano a una herramienta real de scouting.
