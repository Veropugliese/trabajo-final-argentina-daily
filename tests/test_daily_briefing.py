import importlib.util
import io
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "daily_briefing.py"
SPEC = importlib.util.spec_from_file_location("daily_briefing", MODULE_PATH)
daily = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(daily)


class DailyBriefingTests(unittest.TestCase):
    def test_strip_json_fence(self):
        self.assertEqual(daily.strip_json_fence("```json\n{\"ok\": true}\n```"), '{"ok": true}')

    def test_schedule_uses_local_hour(self):
        now = datetime(2026, 8, 21, 8, 7, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
        with patch.dict(os.environ, {"DAILY_SEND_HOUR": "8"}):
            self.assertTrue(daily.scheduled_for_this_hour(now))

    def test_validate_rejects_missing_schema(self):
        with self.assertRaises(RuntimeError):
            daily.validate_briefing({"noticias": []})

    def test_extracts_gemini_text(self):
        body = {
            "candidates": [
                {"content": {"parts": [{"text": '{"noticias": []}'}]}}
            ]
        }
        self.assertEqual(daily.extract_output_text(body), '{"noticias": []}')

    def test_detects_google_search_grounding(self):
        body = {
            "candidates": [
                {"groundingMetadata": {"webSearchQueries": ["noticias Argentina hoy"]}}
            ]
        }
        self.assertTrue(daily.used_google_search(body))
        self.assertFalse(daily.used_google_search({"candidates": []}))

    def test_request_briefing_uses_gemini_and_google_search(self):
        now = datetime(2026, 8, 21, 8, 0, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
        briefing = {
            "agente": "Argentina Daily Intelligence",
            "fecha_briefing": "2026-08-21",
            "version_contrato": "v3",
            "metadata_corrida": {},
            "resumen_ejecutivo": "Resumen",
            "noticias": [],
        }
        response_body = {
            "candidates": [
                {
                    "content": {"parts": [{"text": json.dumps(briefing)}]},
                    "groundingMetadata": {"webSearchQueries": ["noticias Argentina hoy"]},
                }
            ]
        }
        response = unittest.mock.MagicMock()
        response.__enter__.return_value = io.BytesIO(json.dumps(response_body).encode("utf-8"))
        variables = {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-2.5-flash"}

        with patch.dict(os.environ, variables), patch.object(
            daily.urllib.request, "urlopen", return_value=response
        ) as urlopen:
            self.assertEqual(daily.request_briefing(now), briefing)

        request = urlopen.call_args.args[0]
        self.assertIn("gemini-2.5-flash:generateContent", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "test-key")
        payload = json.loads(request.data)
        self.assertEqual(payload["tools"], [{"googleSearch": {}}])

    def test_send_email_uses_gmail_smtp(self):
        briefing = {"fecha_briefing": "2026-08-21", "noticias": []}
        with tempfile.TemporaryDirectory() as directory:
            attachment = Path(directory) / "briefing.json"
            attachment.write_text("{}", encoding="utf-8")
            credentials = {
                "EMAIL_USERNAME": "emisor@gmail.com",
                "EMAIL_PASSWORD": "app-password",
                "EMAIL_TO": "destino@example.com",
            }
            with patch.dict(os.environ, credentials), patch.object(daily.smtplib, "SMTP") as smtp:
                daily.send_email(briefing, attachment)

        smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=60)
        server = smtp.return_value.__enter__.return_value
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("emisor@gmail.com", "app-password")
        server.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
