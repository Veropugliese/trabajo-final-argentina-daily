# Trabajo final — Agente Argentina, Daily Intelligence

Programación de y con Agentes de IA · MBA UCEMA · 2026 2T

**Vero Pugliese**

Sistema agéntico que genera, todos los días, un briefing ejecutivo de Argentina (economía, política con consecuencia concreta, empresas, PyMEs, consumo, agro — más cobertura obligatoria de Córdoba, Tucumán y Santiago del Estero), usando búsqueda web real y un modelo de lenguaje, con salida en JSON de schema fijo, y lo envía por correo de forma automática todos los días vía GitHub Actions.

Este repositorio continúa un proyecto real que empezó en una entrega anterior de la materia (el contrato de prompt) y lo escala acá a un sistema agéntico completo, con las tres piezas que le faltaban: corridas reales, análisis económico y gobierno/riesgo.

## Mapa del repositorio

| Archivo / carpeta | Qué es |
|---|---|
| [`prompts/system_prompt.md`](prompts/system_prompt.md) | El contrato: identidad, contexto, pipeline de decisión, restricciones, formato de salida y supervisión (L0–L4). Versión vigente (v3). |
| [`prompts/user_prompt.md`](prompts/user_prompt.md) | Plantilla del pedido diario. |
| [`prompts/iteraciones/`](prompts/iteraciones/) | Versiones anteriores del contrato (v1, v2), para comparar antes/después de cada iteración. |
| [`corridas/`](corridas/) | Las corridas reales de este trabajo final: entrada, salida y fecha de cada ejecución, más una corrida extra de comparación de modelos. |
| [`ejemplos/`](ejemplos/) | Corridas anteriores (dos ficticias para mostrar el schema, una real generada con la v1, antes de las iteraciones — la que expuso los problemas que se corrigieron). |
| [`scripts/daily_briefing.py`](scripts/daily_briefing.py) | El programa pensado para producción: llama a Gemini con Google Search, valida el JSON, genera el HTML y envía el correo. Requiere Python (no instalado en la máquina donde se armó este trabajo final). |
| [`scripts/run_corrida.ps1`](scripts/run_corrida.ps1) | El script que sí se usó para generar las corridas reales de `corridas/` en PowerShell, sin Python. Soporta búsqueda nativa de Gemini y, cuando esa cuota no está disponible (ver `DECISIONES.md`), un modo con material provisto a mano. |
| [`tests/`](tests/) | Tests del script (parseo, validación de schema, armado del pedido a Gemini, envío de correo). |
| [`.github/workflows/daily-briefing.yml`](.github/workflows/daily-briefing.yml) | Automatización: corre el script todos los días por cron y también a demanda. |
| [`CONFIGURACION_GITHUB_ACTIONS.md`](CONFIGURACION_GITHUB_ACTIONS.md) | Cómo configurar los secretos y variables para que la automatización funcione. |
| [`DECISIONES.md`](DECISIONES.md) | La historia: iteraciones, qué falló, qué se achicó y por qué. |
| [`ANALISIS-ECONOMICO.md`](ANALISIS-ECONOMICO.md) | Costo por corrida, proyección semanal/anual, elección de modelo justificada. |
| [`GOBERNANZA-Y-RIESGO.md`](GOBERNANZA-Y-RIESGO.md) | Qué toca el agente, con qué permisos, qué puede salir mal, quién controla y quién firma. |

## Qué construí

Un sistema agéntico completo, no un prompt suelto: un contrato escrito (`prompts/system_prompt.md` + `prompts/user_prompt.md`, con las seis piezas: rol, contexto, tarea, restricciones, formato, ejemplos), conectado a una herramienta real — búsqueda web en vivo a través de Gemini (`googleSearch`) — que corre sola todos los días por GitHub Actions, valida su propia salida contra un schema JSON fijo, y la envía por correo (Gmail SMTP).

El objetivo es concreto: ahorrarme la lectura diaria de diarios y reportes dispersos, con foco en lo que tiene consecuencia económica o de negocio — incluyendo cobertura de tres provincias (Córdoba, Tucumán, Santiago del Estero) que normalmente no aparecen en los resúmenes nacionales genéricos.

La supervisión está declarada en `prompts/system_prompt.md` §7 con el vocabulario del curso: **L3** — el agente busca, filtra, redacta y envía sin aprobación previa (porque el destino es mi propia casilla, no un tercero), y el control humano está *después*: nadie actúa sobre una noticia del briefing sin abrir la fuente y confirmar el dato ahí. El detalle completo, incluido qué pasa si esto cambia, está en [`GOBERNANZA-Y-RIESGO.md`](GOBERNANZA-Y-RIESGO.md).

## Cómo se lo pedí

1. Para la entrega anterior, pegué un boceto grande de un sistema de dos agentes de noticias (Argentina diario + Global semanal) y le pedí a la IA que separara qué parte era la consigna real. Acordamos construir solo el Agente Argentina Daily, con foco en salida estructurada y comparable entre corridas — ver el detalle en `prompts/iteraciones/` y en `DECISIONES.md`.
2. Escribí el contrato completo (system + user prompt) y lo corrí de verdad con búsqueda web una vez, lo que expuso dos problemas reales (cifras contradictorias entre fuentes, temas sin fuente propia verificable) — dos iteraciones documentadas en `DECISIONES.md`.
3. Para escalarlo a un sistema que corre solo (no a mano en un chat), le pedí que armara el pipeline de software: un script en Python que llama a la API real, valida el JSON, arma el HTML y manda el correo, más el workflow de GitHub Actions que lo dispara todos los días. En el camino cambié de proveedor de modelo (de OpenAI a Gemini) por costo — está en `DECISIONES.md` y en `ANALISIS-ECONOMICO.md`.
4. Para este trabajo final, separé el proyecto en su propio repositorio (para no tocar la entrega ya evaluada), reorganicé todo a la estructura obligatoria de la materia (`prompts/`, `corridas/`, `DECISIONES.md`), corrí el contrato de verdad para tener las corridas reales que pide la consigna, y armé el análisis económico y de gobierno que todavía faltaban.

## Qué funciona

- El contrato cubre explícitamente las seis piezas pedidas, cada una en su propia sección numerada de `prompts/system_prompt.md`.
- La salida es JSON con schema fijo — comparable campo a campo entre corridas (ver `corridas/`).
- El pipeline de decisión es agéntico, no una redacción libre: el agente decide qué descarta (`noticias_descartadas`), qué agrupa como duplicado (`grupos_duplicados`) y qué fuentes falló, y lo deja registrado en la salida.
- La herramienta es real: el contrato está diseñado para llamar a la API de Gemini con `googleSearch` activo y **rechazar** la respuesta si el modelo no usó búsqueda real (`used_google_search`) — no puede fabricar un briefing sin buscar de verdad. Las corridas oficiales de este trabajo final se hicieron con material recolectado por búsqueda web real hecha por fuera (la cuenta de Gemini usada no tiene la cuota de grounding habilitada todavía — ver `DECISIONES.md`), pero el pipeline agéntico (clasificar, puntuar, descartar, deduplicar) corrió igual sobre datos 100% reales, y en la corrida 1 incluí a propósito una noticia de 11 días de antigüedad como caso de prueba, con una nota que planteaba la duda sin resolverla ("evaluar si corresponde incluirla... o descartarla por antigüedad" — ver `corridas/material_recolectado_1.md`, ítem 5): el pipeline resolvió la duda solo, aplicando su propia regla de ventana de 36 horas, y descartó la noticia citando exactamente ese motivo.
- El sistema está pensado para correr solo: GitHub Actions lo dispara todos los días (`cron: "7 * * * *"`, comparado contra la hora configurada) y también permite disparo manual para pruebas — hoy esa automatización específica está bloqueada por la cuota de Google, no por el diseño (ver `GOBERNANZA-Y-RIESGO.md`, riesgo 5).
- Hay tests (`tests/test_daily_briefing.py`) que cubren el parseo de la respuesta de Gemini, la validación del schema, la detección de uso real de búsqueda, y el envío de correo.

## Qué falta o qué falló

- **La cuota de `googleSearch` de Gemini no está habilitada en la cuenta usada para este trabajo final** — probado con dos API keys y cinco modelos distintos, mismo resultado (429, cuota de grounding en 0). Mientras eso no se resuelva, la automatización diaria de `scripts/daily_briefing.py` fallaría en producción. Las corridas de `corridas/` se hicieron con el modo de contingencia que el propio contrato ya preveía (material provisto a mano) — ver `DECISIONES.md`, iteración 4, y `GOBERNANZA-Y-RIESGO.md`, riesgo 5.
- El Agente Global (semanal, geopolítica/mercados/tecnología) sigue fuera de alcance — decisión tomada desde la entrega anterior y sostenida acá para poder cerrar bien el análisis económico y de gobierno de un solo agente en el tiempo disponible.
- No hay reintentos automáticos si Gemini devuelve un JSON inválido o si `googleSearch` no se dispara — el script corta la ejecución con un error legible (`RuntimeError`) y GitHub Actions lo reporta como corrida fallida, pero no reintenta solo. Ver `GOBERNANZA-Y-RIESGO.md`.
- El envío por correo asume una sola casilla de destino (`EMAIL_TO`) de uso interno — no está pensado para reenvío directo a terceros sin revisión. Ver el detalle de este riesgo en `GOBERNANZA-Y-RIESGO.md`.
- Ver `DECISIONES.md` para las fallas puntuales encontradas durante las corridas reales de este trabajo final (incluido un bug de PowerShell y una alucinación de fuentes del modelo grande) y qué se hizo con cada una.

## Qué aprendí

Que un contrato de agente no se termina de escribir en el escritorio: se termina de escribir corriéndolo y viendo qué decisión tuve que tomar "a criterio" sin que el contrato me lo dijera (dos fuentes contradictorias, un tema sin fuente propia) — esa decisión improvisada es exactamente lo que hay que convertir en regla escrita.

También aprendí que "sistema agéntico" y "prompt bien escrito" no son lo mismo: un contrato prolijo que se corre a mano en un chat no es un sistema — lo que lo convirtió en sistema fue conectarlo a una herramienta real, hacerlo correr solo, y bancarse las preguntas incómodas que este trabajo final obliga a responder y que un prompt nunca te obliga a contestar: cuánto cuesta, qué puede salir mal, y quién firma cuando algo sale mal.
