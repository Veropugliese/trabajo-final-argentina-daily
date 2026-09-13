# Gobierno y riesgo

## Qué sistemas toca el agente, y con qué permisos

| Sistema | Acceso | Alcance |
|---|---|---|
| **Google Search** (vía `googleSearch` de Gemini) | Lectura | Búsqueda web pública. El agente no puede escribir ni modificar nada ahí — solo consulta. |
| **API de Gemini** (Google AI) | Escritura de la solicitud, lectura de la respuesta | Se manda el contrato completo (`system_prompt.md` + `user_prompt.md`) más la fecha del día. La clave (`GEMINI_API_KEY`) vive como secreto de GitHub Actions, nunca en el repositorio. |
| **Gmail, vía SMTP** | Escritura (envío) | El agente **envía** un correo a `EMAIL_TO`, con una contraseña de aplicación (`EMAIL_PASSWORD`) que solo tiene permiso de enviar desde esa casilla — no de leerla ni administrarla. No lee la bandeja de entrada, no borra nada. |
| **GitHub Actions** | Ejecución programada | Corre en un runner efímero de GitHub, con permiso `contents: read` únicamente (declarado en el workflow) — no puede escribir de vuelta al repositorio. |
| **Repositorio de GitHub** | Almacenamiento del artefacto | Cada corrida se guarda como artifact de Actions (30 días de retención) y, para las corridas oficiales de este trabajo final, también como archivo versionado en `corridas/`. |

`EMAIL_TO` está configurado como una casilla de uso **interno** (de la propia responsable del sistema), no de un tercero. Esto es una decisión de diseño, no un detalle: es lo que permite declarar L3 (ver `prompts/system_prompt.md` §7) en vez de L4. Ver riesgo 1 más abajo.

## Modos de falla concretos

**1. `EMAIL_TO` termina apuntando a un tercero sin agregar un paso de aprobación.**
Qué pasa: el agente pasaría a enviar contenido no revisado (que puede tener una fuente descartada por error, o una discrepancia entre cifras que el propio contrato marca pero no resuelve) directamente a una persona externa, sin que nadie lo haya leído antes. Eso convierte un L3 razonable en un L4 no controlado. Mitigación: el README y `CONFIGURACION_GITHUB_ACTIONS.md` dejan explícito que `EMAIL_TO` debe ser una casilla propia; si algún día se necesita mandarlo a un tercero, hay que agregar antes un paso de revisión humana (por ejemplo, generar sin `--send` y reenviar a mano tras leerlo).

**2. Gemini devuelve un JSON que no cumple el schema, o no usa búsqueda real.**
Qué pasa: `validate_briefing()` y `used_google_search()` cortan la ejecución con un `RuntimeError` antes de guardar o enviar nada — no se produce ni un correo ni un artefacto corrupto. GitHub Actions marca la corrida como fallida (exit code 1) y queda visible en la pestaña Actions. No hay reintento automático: si pasa un día entero sin briefing, nadie se entera salvo que alguien revise el repositorio. Mitigación pendiente (ver "Qué falta" en el README): agregar una notificación (por ejemplo, un correo de alerta) cuando la corrida programada falla, en vez de fallar en silencio.

**3. Una fuente da una cifra vieja o descontextualizada y el agente la presenta como novedad.**
Qué pasa: el contrato pide ventana de 24–36 horas y fecha de publicación por noticia, pero no hay una verificación programática de esa fecha — depende de que el modelo la calcule bien. Si se equivoca, una noticia vieja podría colarse como si fuera de hoy. Mitigación: el punto de control humano (ver abajo) exige abrir la fuente antes de actuar sobre cualquier dato, lo que expone este tipo de error antes de que tenga consecuencia.

**4. Fuga de la API key o de la contraseña de aplicación de Gmail.**
Qué pasa: quien la obtenga podría generar corridas en nombre del sistema o, en el caso de la contraseña de Gmail, enviar correo desde esa casilla. Mitigación: ambas viven únicamente como secretos de GitHub Actions (`secrets.GEMINI_API_KEY`, `secrets.EMAIL_PASSWORD`), nunca en el código ni en el historial de commits; `.gitignore` excluye cualquier `.env` local. Si alguna vez apareciera una clave expuesta en el repositorio, se trata como incidente de seguridad inmediato: se revoca la clave y se genera una nueva antes de cualquier otra cosa.

**5. La cuota de `googleSearch` de Gemini no está habilitada en la cuenta.**
Qué pasa: pasó de verdad durante la construcción de este trabajo final (ver `DECISIONES.md`, iteración 4) — la cuenta nueva tiene la cuota de "fundamentación de búsqueda" en 0 para toda la familia de modelos vigente, así que el flujo automático con `scripts/daily_briefing.py` fallaría hoy con un `RuntimeError` en cada corrida programada, sin generar ni enviar nada (fallo seguro, no silencioso). Mitigación: el contrato ya preveía un modo sin herramienta ("Opción B" de `user_prompt.md`); mientras la cuota no se habilite, el sistema no puede correr desatendido y necesita que alguien provea el material a mano, lo que rompe la automatización diaria hasta que Google habilite la cuota o se vincule facturación al proyecto correcto.

**6. El modelo alucina una fuente que no existe.**
Qué pasa: se observó de verdad al comparar modelos para `ANALISIS-ECONOMICO.md` — `gemini-3.6-flash`, con el mismo material real que `gemini-3.1-flash-lite`, agregó a `metadata_corrida.fuentes_consultadas` dos medios que no estaban en el material provisto. No llegó a inventar una noticia completa (las dejó en `noticias_descartadas`), pero sí infló la lista de fuentes consultadas. Mitigación: es una razón concreta (no solo de costo) para usar el modelo más chico, que en la misma prueba no alucinó ninguna fuente; de todos modos, ningún modelo está exento de este riesgo, por lo que el punto de control humano de abajo exige verificar la fuente citada, no solo confiar en que "fuentes_consultadas" sea precisa.

## Punto de control humano

Antes de tomar cualquier decisión de negocio a partir de una noticia del briefing (no antes de que el briefing se genere o se envíe): abrir la URL fuente citada en el campo `url` de esa noticia y confirmar ahí el dato — la fecha de publicación, la cifra exacta, y que la fuente sea la que el JSON dice que es. El campo `fuentes_contrastadas` indica cuándo el propio agente ya cruzó más de una fuente, pero eso no reemplaza la lectura humana antes de actuar. El campo `metadata_corrida.noticias_descartadas` también se revisa cuando algo "debería haber salido y no salió" — ahí queda registrado por qué se dejó afuera.

## Quién firma

**Vero Pugliese**, responsable del sistema, firma cada corrida en el sentido de: el proceso corrió como estaba definido, el JSON es válido, y la fuente de cada noticia es verificable. No firma el contenido de cada noticia individual como verdad absoluta — esa verificación puntual es justamente lo que exige el punto de control humano de arriba antes de actuar sobre cualquier dato.
