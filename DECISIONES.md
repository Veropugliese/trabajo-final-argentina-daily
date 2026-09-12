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

## Iteración 4 — corridas reales de este trabajo final

*(Se completa después de ejecutar las tres corridas oficiales en `corridas/` con la v3 del contrato. Si alguna corrida real expone un problema nuevo, se documenta acá con el error textual tal cual salió, siguiendo el mismo formato de las iteraciones anteriores.)*
