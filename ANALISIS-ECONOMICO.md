# Análisis económico

## Precio del modelo

Precios de la API de Gemini consultados en [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) el **12/09/2026**:

| Modelo | Input (por 1M tokens) | Output (por 1M tokens) | Grounding con Google Search |
|---|---|---|---|
| **Gemini 2.5 Flash** (el que usa este agente) | USD 0,30 | USD 2,50 | Gratis hasta 500 solicitudes/día (compartido con Flash-Lite); luego USD 35 cada 1.000 |
| Gemini 2.5 Pro | USD 1,25 (≤200k tokens de prompt) | USD 10,00 (≤200k tokens de prompt) | Gratis hasta 1.500 solicitudes/día; luego USD 35 cada 1.000 |

Con una corrida por día, el uso real de este agente queda **dentro de la cuota gratuita** de Google Search grounding en cualquiera de los dos modelos — el costo real hoy es **USD 0**. Los cálculos de abajo muestran cuánto costaría igual, con precio de tarifa estándar (sin cuota gratuita), para poder proyectar qué pasa si el uso escala (más corridas por día, o un uso que consume la cuota gratuita de grounding).

## Costo por corrida

*(Se completa con los tokens reales que devuelve la API de Gemini en `usageMetadata` — `promptTokenCount` y `candidatesTokenCount` — de las tres corridas guardadas en `corridas/`.)*

| Corrida | Tokens de entrada | Tokens de salida | Costo a tarifa estándar |
|---|---|---|---|
| `corridas/<fecha-1>.md` | — | — | — |
| `corridas/<fecha-2>.md` | — | — | — |
| `corridas/<fecha-3>.md` | — | — | — |
| **Promedio** | — | — | — |

Fórmula: `costo = (tokens_entrada / 1.000.000 × 0,30) + (tokens_salida / 1.000.000 × 2,50)`, en dólares, a tarifa estándar de Gemini 2.5 Flash.

## Proyección a escala

Supuesto de volumen: **1 corrida por día** (la cadencia declarada en el contrato, sección 2 de `prompts/system_prompt.md`).

- Por semana: 7 corridas × costo promedio por corrida.
- Por año: 365 corridas × costo promedio por corrida.

*(Los tres renglones de abajo se completan con el promedio de la tabla anterior.)*

| Periodo | Corridas | Costo estimado (tarifa estándar) |
|---|---|---|
| Semanal | 7 | — |
| Anual | 365 | — |

Estos números son el costo *como si no existiera cuota gratuita* — el peor caso, útil para decidir si el sistema sigue siendo viable si algún día se factura de verdad. El costo real actual, dentro de la cuota gratuita de grounding (hasta 500 solicitudes/día en Flash), es **USD 0** para este volumen de uso.

## Elección de modelo — Flash vs. Pro

**Criterio del curso: el modelo más chico que hace bien la tarea.**

Gemini 2.5 Flash cuesta **~4x menos en input y ~4x menos en output** que Gemini 2.5 Pro a tarifa estándar (USD 0,30 vs. USD 1,25 de entrada; USD 2,50 vs. USD 10,00 de salida), y comparte la misma herramienta de `googleSearch`.

*(Pendiente: correr la misma corrida real con Gemini 2.5 Pro para comparar contra el resultado de Flash y mostrar en qué se diferencian — cuántas noticias encuentra cada uno, si el filtrado de fuente-propia-verificable se respeta igual, si el schema sale idéntico. Esto se completa junto con las corridas oficiales en `corridas/` y se documenta acá con el resultado concreto de la comparación, no solo el argumento de precio.)*
