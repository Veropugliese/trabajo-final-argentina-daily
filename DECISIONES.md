# Decisiones — historia real de la construcción

Este documento cuenta cómo llegó el sistema a su forma actual: qué se probó, qué falló, y qué se cambió en cada paso. Las iteraciones 1 a 3 pasaron durante la construcción del contrato en una entrega anterior de la materia (proyecto propio, distinto de este repositorio); las iteraciones a partir de la 4 son el trabajo hecho específicamente para este trabajo final, con su propio historial de commits en este repo.

## Iteración 1 — cifras contradictorias entre fuentes

**Cuándo:** 21/08/2026, al probar el contrato por primera vez con una corrida real.

**Qué se probó:** correr el contrato v1 (`prompts/iteraciones/system_prompt_v1.md`) con búsqueda web real, para ver si el pipeline de decisión funcionaba con datos reales y no solo con ejemplos ficticios.

**Qué falló:** el v1 no decía qué hacer si dos fuentes daban cifras distintas para el mismo hecho. En la corrida real (`ejemplos/corrida_real_2026-08-21.json`), una fuente con artículo específico y fecha (Infobae) decía que el riesgo país había bajado a 506 puntos; un resumen agregado de otra búsqueda decía que había superado los 530, sin artículo propio verificable detrás. El contrato no daba un criterio — tuve que decidir "a criterio" en el momento (usé la cifra con fuente específica).

**Qué se cambió:** agregué una restricción explícita en el contrato: priorizar la fuente con artículo específico y fecha verificable por sobre afirmaciones agregadas sin fuente clara; si dos cifras son igualmente verificables pero contradictorias, dejar constancia de la discrepancia en vez de elegir en silencio. Ver el diff entre `prompts/iteraciones/system_prompt_v1.md` y `prompts/iteraciones/system_prompt_v2.md`, sección Restricciones.

## Iteración 2 — temas sin fuente propia verificable

**Cuándo:** mismo ciclo, 21/08/2026.

**Qué se probó:** la misma corrida real de la Iteración 1, revisando el paso 6 del pipeline ("Descartar").

**Qué falló:** encontré dos temas relevantes (producción de carne y leche en un congreso agropecuario; interés de mineras en litio) que solo aparecían citados dentro de resúmenes agregados de búsqueda, sin un artículo propio con URL verificable detrás. El contrato v2 decía que había que descartar "lo irrelevante", pero no cubría el caso de un tema mencionado de rebote dentro de la cobertura de otro artículo. Los descarté por precaución, pero otra corrida podría haber decidido incluirlos citando la fuente agregada como si fuera el artículo original — el criterio no estaba escrito, dependía de mi buen juicio ese día.

**Qué se cambió:** sumé al paso 6 del pipeline la regla explícita: descartar cualquier tema sin un artículo propio con URL verificable, aunque haya aparecido mencionado dentro de otro artículo. Esta es la versión vigente (v3, `prompts/system_prompt.md`).

## Iteración 3 — migración de OpenAI a Gemini

**Cuándo:** 21/08/2026, al automatizar el contrato para que corriera solo todos los días.

**Qué se probó:** automatizar el contrato con la API de Responses de OpenAI (`gpt-5.4-mini`, herramienta `web_search`) para que corriera solo, todos los días, vía GitHub Actions.

**Qué falló:** correr esto una vez por día, todos los días, con una API de pago no tiene sentido económico para un proyecto personal que todavía se está validando — el costo recurrente crece sin que haya ingresos ni presupuesto asignado detrás. No fue un error técnico: fue un problema de sostenibilidad del costo para el caso de uso real (ver `ANALISIS-ECONOMICO.md` para la cuenta completa).

**Qué se cambió:** migré `scripts/daily_briefing.py` de la Responses API de OpenAI a la API de Gemini (`gemini-2.5-flash`) con la herramienta `googleSearch`, que tiene cuota gratuita para este volumen de uso. El cambio de proveedor obligó a reescribir el armado del payload, la extracción del texto de respuesta y el chequeo de que la búsqueda real se haya usado — quedó además como salvaguarda dura: si Gemini no usó Google Search, el script descarta la respuesta con `RuntimeError("Gemini no utilizó Google Search; se descartó el briefing desactualizado")` en vez de aceptar un briefing potencialmente inventado.

## Cambio de alcance — el Agente Global queda afuera

**Cuándo:** decisión tomada el 21/08/2026 y sostenida en este trabajo final.

**Qué se achicó:** el boceto original contemplaba dos agentes — Argentina Daily (diario) y Global Weekly (geopolítica, mercados, IA, tecnología, semanal). Se descartó construir el segundo.

**Por qué:** el foco de la consigna era demostrar un contrato bien construido con salida estructurada y comparable, no la cantidad de agentes. Construir los dos a la vez hubiera diluido el tiempo disponible para hacer bien las cosas que este trabajo final exige de verdad: corridas reales, análisis económico defendible, y gobierno y riesgo pensado en serio — en vez de dos contratos superficiales.

## Iteración 4 — correr el contrato de verdad para este trabajo final

**Cuándo:** 13/09/2026, madrugada — el día de la entrega.

**Qué se probó:** ejecutar `prompts/system_prompt.md` + `prompts/user_prompt.md` de verdad contra la API de Gemini con `googleSearch` real, usando un script en PowerShell (`scripts/run_corrida.ps1`) porque esta máquina no tiene Python instalado.

**Qué falló (tres problemas reales, en cadena):**

1. **Bug de PowerShell 5.1.** El primer intento tiró esto tal cual:
   ```
   ConvertTo-Json : Se produjo una excepción de tipo 'System.OutOfMemoryException'.
   En C:\Users\vero\Desktop\vero\trabajo-final\scripts\run_corrida.ps1: 62 Carácter: 5
   + } | ConvertTo-Json -Depth 10 -Compress
   ```
   `ConvertTo-Json` en Windows PowerShell 5.1 tiene un bug conocido de rendimiento/memoria al escapar strings largos (el system prompt tiene varios miles de caracteres). No es un error del contrato, es del entorno de ejecución.

2. **Modelos dados de baja para cuentas nuevas.** Con el JSON arreglado a mano, `gemini-2.5-flash` (el modelo original del contrato) devolvió:
   ```
   {"error":{"code":404,"message":"This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash..."}}
   ```
   Lo mismo pasó después con `gemini-2.5-flash-lite`. Toda la familia 2.5 quedó inservible para esta cuenta.

3. **Cuota de búsqueda en cero para la familia 3.x.** Cambiando a `gemini-3.6-flash` (como sugería el error anterior), la respuesta fue:
   ```
   {"error":{"code":429,"message":"You exceeded your current quota, please check your plan and billing details...","status":"RESOURCE_EXHAUSTED"}}
   ```
   Se confirmó con el panel de cuotas de Google (ai.dev/rate-limit) que la "Fundamentación de la búsqueda" (grounding) para toda la familia Gemini 3.x está en **0/0** en esta cuenta nueva — no es un límite que se gaste, es un límite que no está habilitado. Se probó con dos API keys distintas y cinco modelos (`gemini-3.6-flash`, `gemini-flash-latest`, `gemini-3.1-flash-lite`, entre otros): mismo resultado. Un llamado sin herramientas (`generateContent` puro, sin `googleSearch`) sí funcionó con la misma key, aislando el problema a la cuota de grounding específicamente, no a la cuenta en general ni a la key.

**Qué se cambió:** el contrato ya preveía este escenario — `user_prompt.md` tiene una "Opción B: sin herramientas, con material provisto" pensada exactamente para cuando no hay búsqueda activa. Se usó esa opción: la búsqueda la hice yo por fuera (con mis propias herramientas de navegación), armé el material recolectado con título, medio, URL, fecha y extracto de cada artículo real, y se lo pasé al contrato para que hiciera el trabajo agéntico real (clasificar, puntuar, descartar, deduplicar) sobre datos reales. `scripts/run_corrida.ps1` quedó con un flag `-MaterialFile` para soportar este modo sin tocar el contrato. La cuota de Google sigue siendo un problema pendiente para cuando el sistema tenga que correr solo todos los días — ver `GOBERNANZA-Y-RIESGO.md`, riesgo 5.

**Resultado, ya con datos reales:** las corridas en `corridas/` muestran que el pipeline de decisión funciona con material real: en la corrida 1 incluí a propósito una noticia de Córdoba de 11 días de antigüedad, con una nota que planteaba la duda sin resolverla ("evaluar si corresponde incluirla... o descartarla por antigüedad"). El pipeline resolvió esa duda solo, aplicando su propia regla de ventana de 36 horas, y la descartó citando exactamente ese motivo — sin que la nota le dijera qué hacer, solo que había algo para decidir.

## Iteración 5 — la comparación de modelos expuso una alucinación

**Cuándo:** 13/09/2026, misma madrugada.

**Qué se probó:** correr exactamente el mismo material recolectado (`corridas/material_recolectado_2.md`) con dos modelos distintos — `gemini-3.1-flash-lite` (chico) y `gemini-3.6-flash` (grande) — para poder justificar la elección de modelo con una prueba real, no solo con el argumento de precio (ver `ANALISIS-ECONOMICO.md`).

**Qué falló:** el modelo grande (`gemini-3.6-flash`) devolvió, en `metadata_corrida.fuentes_consultadas`, dos medios que **no existen en el material provisto**: "La Voz del Interior (Córdoba)" y "El Liberal (Santiago del Estero)". El material que le pasé decía explícitamente "no se encontró material propio verificable para Córdoba ni Santiago del Estero" — el modelo grande inventó fuentes para esas provincias igual, aunque después, para las noticias en sí, no llegó a fabricar una noticia falsa (las dejó correctamente en `noticias_descartadas`). El modelo chico (`gemini-3.1-flash-lite`), con el mismo material, no inventó ninguna fuente: su lista de `fuentes_consultadas` coincide exactamente con los 6 medios reales del material.

**Qué se cambió:** esto se convirtió en la evidencia central de `ANALISIS-ECONOMICO.md` para justificar `gemini-3.1-flash-lite` como el modelo del contrato: no es solo que sea ~3x más barato, es que en esta prueba concreta fue **más confiable** que el modelo grande, que alucinó. Es una falla real y no resuelta del modelo grande — no se investigó más a fondo por el tiempo disponible, pero queda documentada como razón concreta (no una preferencia genérica) para la elección de modelo.
