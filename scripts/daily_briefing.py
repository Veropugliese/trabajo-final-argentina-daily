#!/usr/bin/env python3
"""Genera el briefing con Gemini y opcionalmente lo envía por SMTP."""

from __future__ import annotations

import argparse
import html
import json
import os
import smtplib
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
DEFAULT_TIMEZONE = "America/Argentina/Buenos_Aires"
REQUIRED_TOP_LEVEL_KEYS = {
    "agente",
    "fecha_briefing",
    "version_contrato",
    "metadata_corrida",
    "resumen_ejecutivo",
    "noticias",
}


def env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.environ.get(name) or default
    if required and not value:
        raise RuntimeError(f"Falta la variable o secreto obligatorio {name}")
    return value or ""


def local_now() -> datetime:
    timezone_name = env("TIME_ZONE", DEFAULT_TIMEZONE)
    try:
        return datetime.now(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(f"Zona horaria inválida: {timezone_name}") from exc


def scheduled_for_this_hour(now: datetime) -> bool:
    raw_hour = env("DAILY_SEND_HOUR", "8")
    try:
        hour = int(raw_hour)
    except ValueError as exc:
        raise RuntimeError("DAILY_SEND_HOUR debe ser un entero entre 0 y 23") from exc
    if not 0 <= hour <= 23:
        raise RuntimeError("DAILY_SEND_HOUR debe ser un entero entre 0 y 23")
    return now.hour == hour


def build_user_prompt(now: datetime) -> str:
    template = (ROOT / "user_prompt.md").read_text(encoding="utf-8")
    date_argentina = now.strftime("%d/%m/%Y")
    template = template.replace("{{FECHA}}", date_argentina)
    template = template.replace("{{VENTANA_HORAS, default 36}}", env("WINDOW_HOURS", "36"))
    template = template.replace(
        "{{PEGAR_AQUI_LISTA_DE_ARTICULOS_RECOLECTADOS}}",
        "No aplica: usá las herramientas de búsqueda web disponibles.",
    )
    return template


def request_briefing(now: datetime) -> dict[str, Any]:
    api_key = env("GEMINI_API_KEY", required=True)
    model = env("GEMINI_MODEL", "gemini-2.5-flash")
    system_prompt = (ROOT / "system_prompt.md").read_text(encoding="utf-8")
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": build_user_prompt(now)}],
            }
        ],
        "tools": [{"googleSearch": {}}],
        "generationConfig": {"temperature": 0.2},
    }
    encoded_model = urllib.parse.quote(model, safe="-._")
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{encoded_model}:generateContent",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            body = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API respondió HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"No se pudo conectar con Gemini API: {exc.reason}") from exc

    if not used_google_search(body):
        raise RuntimeError("Gemini no utilizó Google Search; se descartó el briefing desactualizado")
    output_text = extract_output_text(body)
    if not output_text:
        raise RuntimeError("Gemini API no devolvió texto en la respuesta")
    try:
        briefing = json.loads(strip_json_fence(output_text))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"La salida del agente no es JSON válido: {exc}") from exc
    validate_briefing(briefing)
    return briefing


def extract_output_text(body: dict[str, Any]) -> str:
    chunks: list[str] = []
    for candidate in body.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if part.get("text") and not part.get("thought"):
                chunks.append(part["text"])
    return "\n".join(chunks)


def used_google_search(body: dict[str, Any]) -> bool:
    return any(
        candidate.get("groundingMetadata", {}).get("webSearchQueries")
        for candidate in body.get("candidates", [])
    )


def strip_json_fence(text: str) -> str:
    value = text.strip()
    if value.startswith("```json") and value.endswith("```"):
        return value[7:-3].strip()
    if value.startswith("```") and value.endswith("```"):
        return value[3:-3].strip()
    return value


def validate_briefing(briefing: Any) -> None:
    if not isinstance(briefing, dict):
        raise RuntimeError("El briefing debe ser un objeto JSON")
    missing = REQUIRED_TOP_LEVEL_KEYS - briefing.keys()
    if missing:
        raise RuntimeError(f"Faltan claves obligatorias: {', '.join(sorted(missing))}")
    if not isinstance(briefing["noticias"], list):
        raise RuntimeError("La clave noticias debe contener una lista")
    for index, item in enumerate(briefing["noticias"], start=1):
        if not isinstance(item, dict) or not item.get("titulo") or not item.get("url"):
            raise RuntimeError(f"La noticia {index} no tiene título o URL")


def save_briefing(briefing: dict[str, Any], now: datetime) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"briefing_{now:%Y-%m-%d}.json"
    path.write_text(json.dumps(briefing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def render_html(briefing: dict[str, Any]) -> str:
    summary = html.escape(str(briefing.get("resumen_ejecutivo", ""))).replace("\n", "<br>")
    cards = []
    for item in briefing.get("noticias", []):
        title = html.escape(str(item.get("titulo", "Sin título")))
        url = html.escape(str(item.get("url", "")), quote=True)
        source = html.escape(str(item.get("fuente", "")))
        region = html.escape(str(item.get("region", "")))
        category = html.escape(str(item.get("categoria", "")))
        digest = html.escape(str(item.get("resumen", "")))
        importance = html.escape(str(item.get("por_que_importa", "")))
        score = html.escape(str(item.get("score_relevancia", "")))
        cards.append(
            f"<article style='margin:24px 0;padding:18px;border:1px solid #ddd;border-radius:10px'>"
            f"<h2 style='margin-top:0;font-size:20px'><a href='{url}'>{title}</a></h2>"
            f"<p><strong>{source}</strong> · {region} · {category} · Relevancia {score}/100</p>"
            f"<p>{digest}</p><p><strong>Por qué importa:</strong> {importance}</p></article>"
        )
    date = html.escape(str(briefing.get("fecha_briefing", "")))
    return (
        "<!doctype html><html><body style='font-family:Arial,sans-serif;max-width:760px;margin:auto;"
        "padding:24px;color:#202124'><h1>Argentina Daily Intelligence</h1>"
        f"<p style='color:#666'>{date}</p><section style='background:#f5f7fa;padding:18px;border-radius:10px'>"
        f"<strong>Resumen ejecutivo</strong><p>{summary}</p></section>{''.join(cards)}"
        "<p style='color:#777;font-size:12px'>Generado automáticamente. Verificá las fuentes antes de tomar decisiones.</p>"
        "</body></html>"
    )


def render_text(briefing: dict[str, Any]) -> str:
    lines = [
        "ARGENTINA DAILY INTELLIGENCE",
        str(briefing.get("fecha_briefing", "")),
        "",
        str(briefing.get("resumen_ejecutivo", "")),
        "",
    ]
    for item in briefing.get("noticias", []):
        lines.extend(
            [
                str(item.get("titulo", "Sin título")),
                f"{item.get('fuente', '')} · {item.get('region', '')} · {item.get('categoria', '')}",
                str(item.get("resumen", "")),
                f"Por qué importa: {item.get('por_que_importa', '')}",
                str(item.get("url", "")),
                "",
            ]
        )
    return "\n".join(lines)


def send_email(briefing: dict[str, Any], attachment: Path) -> None:
    # Gmail no admite la contraseña normal de la cuenta por SMTP. EMAIL_PASSWORD
    # debe contener una contraseña de aplicación generada en la cuenta de Google.
    username = env("EMAIL_USERNAME", required=True)
    password = env("EMAIL_PASSWORD", required=True)
    recipient = env("EMAIL_TO", required=True)

    message = EmailMessage()
    message["Subject"] = f"Argentina Daily Intelligence — {briefing.get('fecha_briefing', '')}"
    message["From"] = username
    message["To"] = recipient
    message.set_content(render_text(briefing))
    message.add_alternative(render_html(briefing), subtype="html")
    message.add_attachment(
        attachment.read_bytes(),
        maintype="application",
        subtype="json",
        filename=attachment.name,
    )

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(username, password)
        server.send_message(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Enviar el briefing por correo")
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Ejecutar solamente si coincide con DAILY_SEND_HOUR en TIME_ZONE",
    )
    parser.add_argument("--validate-only", type=Path, help="Validar un JSON existente y salir")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.validate_only:
        validate_briefing(json.loads(args.validate_only.read_text(encoding="utf-8")))
        print(f"JSON válido: {args.validate_only}")
        return 0

    now = local_now()
    if args.scheduled and not scheduled_for_this_hour(now):
        print(
            f"No corresponde ejecutar: hora local {now:%H:%M}; "
            f"DAILY_SEND_HOUR={env('DAILY_SEND_HOUR', '8')}."
        )
        return 0

    briefing = request_briefing(now)
    output = save_briefing(briefing, now)
    print(f"Briefing guardado en {output}")
    if args.send:
        send_email(briefing, output)
        print("Correo enviado correctamente")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # GitHub Actions necesita un error legible y exit code != 0.
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
