# Configuración de GitHub Actions

El repositorio queda preparado para generar el briefing con Gemini, buscar noticias con Google Search, validar el JSON, crear una versión HTML legible, enviarla por correo y conservar el JSON como artefacto durante 30 días.

## Lo que debe hacer manualmente el responsable de GitHub

1. Confirmar que el workflow esté en `main`. GitHub solo ejecuta automáticamente los eventos `schedule` de workflows presentes en la rama predeterminada.
2. En GitHub, abrir **Settings → Secrets and variables → Actions**.
3. Crear estos **Repository secrets**:
   - `GEMINI_API_KEY`: clave gratuita creada en [Google AI Studio](https://aistudio.google.com/app/apikey). No guardarla en un archivo del repositorio.
   - `EMAIL_USERNAME`: cuenta Gmail desde la cual se envía (dirección completa).
   - `EMAIL_PASSWORD`: contraseña de aplicación de 16 caracteres de esa cuenta de Google. No usar la contraseña normal ni guardarla en un archivo del repositorio.
   - `EMAIL_TO`: dirección destinataria completa, confirmada y sin espacios.
4. Crear estas **Repository variables**:
   - `DAILY_SEND_HOUR`: hora local de envío, entero de `0` a `23` (por ejemplo, `8`).
   - `TIME_ZONE`: `America/Argentina/Buenos_Aires`.
   - `GEMINI_MODEL`: `gemini-2.5-flash` (se puede cambiar sin editar código).
   - `WINDOW_HOURS`: `36`.
5. Abrir **Actions → Argentina Daily Intelligence → Run workflow** en `main`.
6. Hacer primero una prueba con **Enviar el resultado por correo = false**. Descargar y revisar el artefacto JSON.
7. Repetir la prueba con **Enviar el resultado por correo = true** y confirmar recepción y carpeta de correo no deseado.

## Consideraciones importantes

- La programación de GitHub Actions no garantiza el minuto exacto; puede demorarse algunos minutos cuando hay alta demanda.
- El workflow se despierta al minuto 7 de cada hora. El script solo genera y envía cuando esa hora coincide con `DAILY_SEND_HOUR` en `TIME_ZONE`; cambiar la hora no requiere editar YAML.
- Una ejecución manual ignora `DAILY_SEND_HOUR`, para permitir pruebas en cualquier momento.
- Gemini 2.5 Flash y Google Search tienen una cuota gratuita sujeta a los límites vigentes de Google. El modelo queda configurable sin editar código.
- El emisor está preparado directamente para Gmail mediante `smtp.gmail.com` con STARTTLS; no hay que configurar servidor, puerto ni remitente.
- Gmail no permite autenticar este tipo de conexión SMTP con la contraseña normal. En la misma cuenta de Google hay que activar la verificación en dos pasos y crear una [contraseña de aplicación](https://myaccount.google.com/apppasswords). No hace falta crear otra cuenta.
- Los secretos nunca se imprimen ni se almacenan en los artefactos.

## Diagnóstico rápido

- `Falta ... GEMINI_API_KEY`: no se creó el secreto o está vacío.
- `HTTP 400` o `403` de Gemini: comprobar que la clave sea válida y tenga acceso a Gemini API.
- `HTTP 429` de Gemini: se alcanzó temporalmente un límite de uso o la cuota gratuita.
- `SMTPAuthenticationError`: comprobar que `EMAIL_USERNAME` sea la dirección Gmail completa y que `EMAIL_PASSWORD` contenga una contraseña de aplicación vigente, no la contraseña normal.
- No se ejecuta diariamente: confirmar que el workflow fue fusionado a `main` y que Actions está habilitado en el repositorio.
