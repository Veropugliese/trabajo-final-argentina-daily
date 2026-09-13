# Corridas oficiales

Tres corridas reales del trabajo final (`2026-09-13_1.md`, `2026-09-13_2.md`, `2026-09-13_3.md`), generadas con la v3 del contrato (`prompts/system_prompt.md`) usando `scripts/run_corrida.ps1`. Cada archivo tiene **entrada** (el `user_prompt.md` completo, con el material real usado esa corrida), **salida** (el JSON tal cual lo devolvió Gemini) y **fecha** (cuándo se ejecutó, con tokens reales de esa corrida).

La cuota de `googleSearch` de Gemini no estaba habilitada en la cuenta usada (ver `../DECISIONES.md`), así que la búsqueda se hizo por fuera, con material real (título, medio, URL, fecha, extracto), y se le pasó al contrato por la "Opción B" que `prompts/user_prompt.md` ya preveía para este escenario. El pipeline agéntico (clasificar, puntuar, descartar, deduplicar) corrió igual sobre datos 100% reales.

También está `2026-09-13_comparacion-flash.md`: la misma entrada de la corrida 2, corrida con un modelo más grande (`gemini-3.6-flash`) para la comparación de modelos de `../ANALISIS-ECONOMICO.md`.
