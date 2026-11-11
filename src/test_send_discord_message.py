import io
import json
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import send_discord_message as sdm
from send_discord_message import (
    DiscordMessageError,
    MessageConfig,
    build_payload,
    config_from_env,
    parse_color,
    parse_fields,
    post_payload,
    run,
    validate_webhook_url,
)

URL = "https://discord.com/api/webhooks/123456/abc_DEF-ghi"
NOW = datetime(2026, 11, 11, 12, 0, 0, tzinfo=timezone.utc)


def http_error(code, body=b"{}"):
    return urllib.error.HTTPError(URL, code, "err", {}, io.BytesIO(body))


def ok_response(status=204):
    response = MagicMock()
    response.status = status
    response.__enter__.return_value = response
    return response


class TestValidateWebhookUrl(unittest.TestCase):
    def test_accepts_discord_urls(self):
        for url in (
            URL,
            "https://discordapp.com/api/webhooks/1/x",
            "https://canary.discord.com/api/v10/webhooks/1/x",
        ):
            validate_webhook_url(url)

    def test_rejects_other_urls(self):
        for url in ("", "https://example.com/api/webhooks/1/x", "nope"):
            with self.assertRaises(DiscordMessageError) as ctx:
                validate_webhook_url(url)
            self.assertNotIn("example.com", str(ctx.exception))


class TestParseColor(unittest.TestCase):
    def test_converts_hex(self):
        self.assertEqual(parse_color("2ea44f"), 0x2EA44F)
        self.assertEqual(parse_color("#2EA44F"), 0x2EA44F)

    def test_rejects_invalid(self):
        for value in ("zzzzzz", "fff", "2ea44f0"):
            with self.assertRaises(DiscordMessageError):
                parse_color(value)


class TestParseFields(unittest.TestCase):
    def test_accepts_valid_fields(self):
        raw = '[{"name": "a", "value": "b", "inline": true}, {"name": "c", "value": "d"}]'
        self.assertEqual(len(parse_fields(raw)), 2)

    def test_rejects_bad_input(self):
        bad = [
            "{",
            "{}",
            '["x"]',
            '[{"name": "a"}]',
            '[{"name": "", "value": "b"}]',
            '[{"name": "a", "value": "b", "inline": "yes"}]',
            '[{"name": "a", "value": "' + "x" * 1025 + '"}]',
            json.dumps([{"name": "a", "value": "b"}] * 26),
        ]
        for raw in bad:
            with self.subTest(raw=raw[:40]):
                with self.assertRaises(DiscordMessageError):
                    parse_fields(raw)


class TestBuildPayload(unittest.TestCase):
    def test_message_only(self):
        payload = build_payload(MessageConfig(message="hi"))
        self.assertEqual(
            payload,
            {"allowed_mentions": {"parse": []}, "content": "hi"},
        )

    def test_full_embed(self):
        config = MessageConfig(
            message="hi",
            username="Bot",
            avatar_url="https://example.com/a.png",
            embed_title="T",
            embed_description="D",
            embed_url="https://example.com",
            embed_color="2ea44f",
            embed_footer="F",
            embed_timestamp=True,
            embed_fields='[{"name": "a", "value": "b", "inline": true}]',
        )
        payload = build_payload(config, now=NOW)
        self.assertEqual(payload["username"], "Bot")
        self.assertEqual(payload["avatar_url"], "https://example.com/a.png")
        self.assertEqual(
            payload["embeds"],
            [{
                "title": "T",
                "description": "D",
                "url": "https://example.com",
                "color": 0x2EA44F,
                "footer": {"text": "F"},
                "timestamp": "2026-11-11T12:00:00Z",
                "fields": [{"name": "a", "value": "b", "inline": True}],
            }],
        )

    def test_embed_only(self):
        payload = build_payload(MessageConfig(embed_title="T"))
        self.assertNotIn("content", payload)
        self.assertEqual(payload["embeds"], [{"title": "T"}])

    def test_special_characters_survive_json(self):
        payload = build_payload(MessageConfig(message='he said "hi"\n$(x)'))
        self.assertEqual(
            json.loads(json.dumps(payload))["content"], 'he said "hi"\n$(x)'
        )

    def test_rejects_empty(self):
        with self.assertRaises(DiscordMessageError):
            build_payload(MessageConfig())

    def test_rejects_over_length_values(self):
        cases = [
            MessageConfig(message="x" * 2001),
            MessageConfig(message="x", username="x" * 81),
            MessageConfig(embed_title="x" * 257),
            MessageConfig(embed_description="x" * 4097),
            MessageConfig(embed_footer="x" * 2049),
        ]
        for config in cases:
            with self.assertRaises(DiscordMessageError):
                build_payload(config)

    def test_rejects_banned_usernames(self):
        for name in ("MyDiscordBot", "clyde", "CLYDE-bot"):
            with self.assertRaises(DiscordMessageError):
                build_payload(MessageConfig(message="x", username=name))

    def test_rejects_embed_over_total_limit(self):
        fields = json.dumps(
            [{"name": "n", "value": "v" * 1000}] * 6
        )
        config = MessageConfig(
            embed_description="d" * 1000, embed_fields=fields
        )
        with self.assertRaises(DiscordMessageError):
            build_payload(config)


class TestConfigFromEnv(unittest.TestCase):
    def test_maps_variables(self):
        config = config_from_env({
            "MESSAGE": "m",
            "EMBED_TIMESTAMP": "true",
            "EMBED_COLOR": "ffffff",
        })
        self.assertEqual(config.message, "m")
        self.assertTrue(config.embed_timestamp)
        self.assertEqual(config.embed_color, "ffffff")

    def test_defaults_to_empty(self):
        config = config_from_env({})
        self.assertEqual(config, MessageConfig())


class TestPostPayload(unittest.TestCase):
    def test_returns_status_on_success(self):
        with patch("urllib.request.urlopen", return_value=ok_response()):
            self.assertEqual(post_payload(URL, {"content": "x"}), 204)

    def test_retries_rate_limit_then_succeeds(self):
        sleeps = []
        responses = [
            http_error(429, b'{"retry_after": 1.5}'),
            ok_response(),
        ]
        with patch("urllib.request.urlopen", side_effect=responses):
            status = post_payload(URL, {}, sleep=sleeps.append)
        self.assertEqual(status, 204)
        self.assertEqual(sleeps, [1.5])

    def test_client_error_fails_without_retry(self):
        calls = []
        with patch(
            "urllib.request.urlopen",
            side_effect=lambda *a, **k: calls.append(1) or (_ for _ in ()).throw(
                http_error(404, b'{"message": "Unknown Webhook"}')
            ),
        ):
            with self.assertRaises(DiscordMessageError) as ctx:
                post_payload(URL, {}, sleep=lambda s: None)
        self.assertEqual(len(calls), 1)
        self.assertIn("404", str(ctx.exception))
        self.assertIn("Unknown Webhook", str(ctx.exception))
        self.assertNotIn("abc_DEF", str(ctx.exception))

    def test_server_error_exhausts_retries(self):
        errors = [http_error(500) for _ in range(sdm.SEND_ATTEMPTS)]
        with patch("urllib.request.urlopen", side_effect=errors):
            with self.assertRaises(DiscordMessageError) as ctx:
                post_payload(URL, {}, sleep=lambda s: None)
        self.assertIn("500", str(ctx.exception))

    def test_network_failure_is_reported_without_url(self):
        failure = urllib.error.URLError("boom " + URL)
        with patch("urllib.request.urlopen", side_effect=failure):
            with self.assertRaises(DiscordMessageError) as ctx:
                post_payload(URL, {}, sleep=lambda s: None)
        self.assertNotIn("abc_DEF", str(ctx.exception))


class TestRun(unittest.TestCase):
    def run_quiet(self, config, env):
        out = io.StringIO()
        with redirect_stdout(out):
            code = run(config, env)
        return code, out.getvalue()

    def test_dry_run_masks_url_and_does_not_send(self):
        with patch("urllib.request.urlopen") as urlopen:
            code, out = self.run_quiet(
                MessageConfig(message="hi"),
                {"WEBHOOK_URL": URL, "DRY_RUN": "true"},
            )
        urlopen.assert_not_called()
        self.assertEqual(code, 0)
        self.assertIn(f"::add-mask::{URL}", out)
        self.assertIn("Dry run", out)

    def test_sends_when_not_dry_run(self):
        with patch("urllib.request.urlopen", return_value=ok_response()):
            code, out = self.run_quiet(
                MessageConfig(message="hi"), {"WEBHOOK_URL": URL}
            )
        self.assertEqual(code, 0)
        self.assertIn("delivered", out)

    def test_validation_failure_returns_error_code(self):
        code, out = self.run_quiet(
            MessageConfig(), {"WEBHOOK_URL": URL, "DRY_RUN": "true"}
        )
        self.assertEqual(code, 1)
        self.assertIn("::error::Nothing to send", out)

    def test_invalid_url_error_does_not_leak_secret(self):
        code, out = self.run_quiet(
            MessageConfig(message="x"),
            {"WEBHOOK_URL": "https://example.com/secret-token"},
        )
        self.assertEqual(code, 1)
        self.assertEqual(out.count("secret-token"), 1)  # only the mask line


if __name__ == "__main__":
    unittest.main()
