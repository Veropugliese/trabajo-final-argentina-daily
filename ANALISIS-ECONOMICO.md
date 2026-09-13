# Análisis económico

## Precio de los modelos

Precios de la API de Gemini consultados en [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) el **13/09/2026** (tarifa estándar, sin cuota gratuita):

| Modelo | Input (por 1M tokens) | Output (por 1M tokens) |
|---|---|---|
| **Gemini 3.1 Flash-Lite** (el que usa el contrato) | USD 0,25 | USD 1,50 |
| Gemini 3.6 Flash (el modelo "grande" comparado) | USD 0,75 | USD 3,75 |

Grounding con Google Search: 5.000 solicitudes gratis por mes (compartidas entre modelos Gemini 3.x), luego USD 14 cada 1.000. En esta cuenta, esa cuota está en 0 hoy — ver `DECISIONES.md`, iteración 4 — así que el costo de grounding no se pudo medir con una corrida real; se documenta como pendiente.

## Costo por corrida (datos reales)

Tokens medidos directamente de `usageMetadata` de la respuesta de Gemini en cada corrida guardada en `corridas/`:

| Corrida | Modelo | Tokens entrada | Tokens salida | Costo (tarifa estándar) |
|---|---|---|---|---|
| `2026-09-13_1.md` | gemini-3.1-flash-lite | 4.267 | 1.588 | USD 0,00345 |
| `2026-09-13_2.md` | gemini-3.1-flash-lite | 4.281 | 2.119 | USD 0,00425 |
| **Promedio (flash-lite)** | | **4.274** | **1.854** | **USD 0,00385** |
| `2026-09-13_comparacion-flash.md` | gemini-3.6-flash | 4.281 | 2.661 | USD 0,01319 |

Fórmula: `costo = (tokens_entrada / 1.000.000 × precio_entrada) + (tokens_salida / 1.000.000 × precio_salida)`.

Ejemplo verificable con la corrida 1: `(4.267 / 1.000.000 × 0,25) + (1.588 / 1.000.000 × 1,50) = 0,0010668 + 0,002382 = USD 0,0034488`.

Con una corrida por día, el grounding de Google Search entra dentro de la cuota gratuita (500-5.000 solicitudes/mes según el modelo) — el costo real de producción, una vez habilitada esa cuota, seguiría siendo prácticamente **USD 0** para este volumen. Los números de la tabla son a tarifa de pago completa, el escenario "peor caso" sin ningún beneficio de cuota gratuita.

## Proyección a escala

Supuesto de volumen: **1 corrida por día** (la cadencia declarada en `prompts/system_prompt.md`, sección 2), usando el promedio real de `gemini-3.1-flash-lite` (USD 0,00385/corrida):

| Periodo | Corridas | Costo estimado (tarifa estándar, sin cuota gratis) |
|---|---|---|
| Semanal | 7 | USD 0,027 |
| Anual | 365 | USD 1,41 |

Si además se agrega el envío por correo (SMTP de Gmail, sin costo) y se supera la cuota gratuita de grounding, sumar USD 14 cada 1.000 corridas extra — a 1 corrida/día eso tardaría más de 13 años en superarse, así que no es un factor relevante a esta escala.

## Elección de modelo — con prueba real, no solo argumento de precio

**Criterio del curso: el modelo más chico que hace bien la tarea.**

Se corrió exactamente el mismo material real (`corridas/material_recolectado_2.md`) con los dos modelos, y se comparan las salidas:

| | Gemini 3.1 Flash-Lite (chico) | Gemini 3.6 Flash (grande) |
|---|---|---|
| Costo de esta corrida | USD 0,00425 | USD 0,01319 (~3,1x más caro) |
| Noticias incluidas | 6 | 6 |
| `fuentes_consultadas` | 6 fuentes, **todas reales** (coinciden exactamente con el material provisto) | 8 fuentes — **2 inventadas** ("La Voz del Interior", "El Liberal"), que no existen en el material |
| Validación de schema | OK | OK |

El modelo grande no solo cuesta ~3 veces más: en esta prueba concreta **alucinó dos fuentes que no le di**, a pesar de que el material decía explícitamente que no había cobertura verificable para esas dos provincias. El modelo chico no inventó ninguna. Esto no es una preferencia genérica por lo barato — es evidencia directa de que, para esta tarea, el modelo grande fue *menos* confiable, no más. Por eso el contrato usa `gemini-3.1-flash-lite`. El detalle completo de este hallazgo está en `DECISIONES.md`, iteración 5.

## Qué falta

No se pudo medir el costo real de la búsqueda con `googleSearch` nativo de Gemini porque la cuota de grounding de esta cuenta está en 0 (ver `DECISIONES.md`). Cuando esa cuota se habilite, correspondería sumar el costo de grounding (gratis hasta 5.000/mes, después USD 14/1.000) a esta cuenta — a 1 corrida/día, sigue sin ser un costo relevante.
