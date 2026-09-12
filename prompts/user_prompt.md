# User Prompt — pedido puntual del día

Esto se manda junto con el `system_prompt.md` (como mensaje de usuario, después del system prompt). Es la plantilla que se repite cada día — solo cambian los valores entre `{{ }}`.

---

Generá el briefing ejecutivo de Argentina correspondiente al **{{FECHA}}** (formato DD/MM/YYYY), siguiendo exactamente el contrato del system prompt (pipeline, restricciones y formato JSON fijo).

**Ventana temporal**: noticias de las últimas {{VENTANA_HORAS, default 36}} horas.

**Cobertura obligatoria a verificar hoy**: panorama nacional + búsqueda específica en Córdoba, Tucumán y Santiago del Estero. Si alguna de las tres no tiene novedades relevantes hoy, dejala fuera de `noticias` — no la inventes — pero mencioná igual en `metadata_corrida.noticias_descartadas` si evaluaste algo de esa provincia y no llegó al umbral.

**Fuentes disponibles para esta corrida** *(elegir una opción según el entorno de ejecución)*:

- **Opción A — con herramientas de búsqueda/navegación activas**: usalas para cubrir medios nacionales, económicos, empresariales y provinciales (Córdoba, Tucumán, Santiago del Estero). Priorizá fuentes primarias (organismos públicos, reguladores, empresas) cuando exista un anuncio oficial.
- **Opción B — sin herramientas, con material provisto**: a continuación pego el material recolectado hoy (título, medio, URL, fecha, texto o extracto de cada artículo). Trabajá **exclusivamente** con este material, no asumas que buscaste nada más:

```
{{PEGAR_AQUI_LISTA_DE_ARTICULOS_RECOLECTADOS}}
```

**Cantidad esperada de noticias**: aproximadamente 10, flexible según la jornada (menos si el día fue tranquilo, más si fue excepcional). Priorizá calidad y relevancia sobre completar el número.

**Salida**: únicamente el JSON definido en el system prompt, sin texto adicional antes o después.
