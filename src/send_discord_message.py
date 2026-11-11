"""Validate and send a message or embed to a Discord webhook.

Used by the send-discord-message.yml reusable workflow. Configuration is read
from environment variables so that untrusted values (messages, release notes)
never get interpolated into a shell script. The webhook URL is never printed.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

MAX_CONTENT = 2000
MAX_USERNAME = 80
MAX_TITLE = 256
MAX_DESCRIPTION = 4096
MAX_FOOTER = 2048
MAX_FIELDS = 25
MAX_FIELD_NAME = 256
MAX_FIELD_VALUE = 1024
MAX_EMBED_TOTAL = 6000

# Discord rejects usernames containing these substrings.
BANNED_USERNAME_PARTS = ("clyde", "discord")

WEBHOOK_URL_PATTERN = re.compile(
    r"^https://(canary\.|ptb\.)?(discord|discordapp)\.com"
    r"/api(/v[0-9]+)?/webhooks/[0-9]+/[A-Za-z0-9_-]+$"
)
COLOR_PATTERN = re.compile(r"^[0-9a-fA-F]{6}$")

SEND_ATTEMPTS = 4
REQUEST_TIMEOUT_SECONDS = 30


class DiscordMessageError(Exception):
    """Raised when inputs are invalid or Discord does not accept the message."""


@dataclass
class MessageConfig:
    """Everything that can go into one webhook call. Empty means unset."""

    message: str = ""
    username: str = ""
    avatar_url: str = ""
    embed_title: str = ""
    embed_description: str = ""
    embed_url: str = ""
    embed_color: str = ""
    embed_footer: str = ""
    embed_timestamp: bool = False
    embed_fields: str = ""


def check_length(name, value, maximum):
    """Fail if value is longer than Discord allows for name."""
    if len(value) > maximum:
        raise DiscordMessageError(
            f"{name} is {len(value)} characters; Discord allows at most "
            f"{maximum}."
        )


def validate_webhook_url(url):
    """Fail unless url looks like a Discord webhook URL. Never echoes it."""
    if not url:
        raise DiscordMessageError(
            "The webhook-url secret is empty or missing."
        )
    if not WEBHOOK_URL_PATTERN.match(url):
        raise DiscordMessageError(
            "The webhook-url secret is not a valid Discord webhook URL."
        )


def parse_color(value):
    """Convert a hex color such as '#2ea44f' to Discord's integer form."""
    color = value.lstrip("#")
    if not COLOR_PATTERN.match(color):
        raise DiscordMessageError(
            "embed-color must be a 6 digit hex color such as 2ea44f."
        )
    return int(color, 16)


def parse_fields(raw):
    """Parse and validate the embed-fields JSON array."""
    try:
        fields = json.loads(raw)
    except json.JSONDecodeError as error:
        raise DiscordMessageError(
            f"embed-fields is not valid JSON: {error}."
        ) from error
    if not isinstance(fields, list) or len(fields) > MAX_FIELDS:
        raise DiscordMessageError(
            f"embed-fields must be a JSON array of at most {MAX_FIELDS} "
            "objects."
        )
    for index, field in enumerate(fields):
        label = f"embed-fields[{index}]"
        if not isinstance(field, dict):
            raise DiscordMessageError(f"{label} must be an object.")
        for key, maximum in (("name", MAX_FIELD_NAME),
                             ("value", MAX_FIELD_VALUE)):
            text = field.get(key)
            if not isinstance(text, str) or not text:
                raise DiscordMessageError(
                    f"{label}.{key} must be a non-empty string."
                )
            check_length(f"{label}.{key}", text, maximum)
        if not isinstance(field.get("inline", False), bool):
            raise DiscordMessageError(f"{label}.inline must be a boolean.")
    return fields


def validate_username(username):
    """Fail if Discord would reject the username override."""
    lowered = username.lower()
    for part in BANNED_USERNAME_PARTS:
        if part in lowered:
            raise DiscordMessageError(
                "username must not contain 'clyde' or 'discord'; Discord "
                "rejects those names."
            )


def build_embed(config, now=None):
    """Build the embed object, or None when no embed input is set."""
    fields = parse_fields(config.embed_fields) if config.embed_fields else []
    color = parse_color(config.embed_color) if config.embed_color else None

    check_length("embed-title", config.embed_title, MAX_TITLE)
    check_length(
        "embed-description", config.embed_description, MAX_DESCRIPTION
    )
    check_length("embed-footer", config.embed_footer, MAX_FOOTER)

    embed = {}
    if config.embed_title:
        embed["title"] = config.embed_title
    if config.embed_description:
        embed["description"] = config.embed_description
    if config.embed_url:
        embed["url"] = config.embed_url
    if color is not None:
        embed["color"] = color
    if config.embed_footer:
        embed["footer"] = {"text": config.embed_footer}
    if config.embed_timestamp:
        moment = now or datetime.now(timezone.utc)
        embed["timestamp"] = moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    if fields:
        embed["fields"] = fields

    total = (
        len(config.embed_title)
        + len(config.embed_description)
        + len(config.embed_footer)
        + sum(len(f["name"]) + len(f["value"]) for f in fields)
    )
    if total > MAX_EMBED_TOTAL:
        raise DiscordMessageError(
            f"The embed contains {total} characters; Discord allows at most "
            f"{MAX_EMBED_TOTAL} in total."
        )
    return embed or None


def build_payload(config, now=None):
    """Validate config and return the JSON body to post to the webhook."""
    check_length("message", config.message, MAX_CONTENT)
    check_length("username", config.username, MAX_USERNAME)
    validate_username(config.username)

    embed = build_embed(config, now)
    if not config.message and embed is None:
        raise DiscordMessageError(
            "Nothing to send: set message or at least one embed input."
        )

    # An empty allowed_mentions means content can never ping anyone.
    payload = {"allowed_mentions": {"parse": []}}
    if config.message:
        payload["content"] = config.message
    if config.username:
        payload["username"] = config.username
    if config.avatar_url:
        payload["avatar_url"] = config.avatar_url
    if embed is not None:
        payload["embeds"] = [embed]
    return payload


def retry_delay(error, attempt):
    """Seconds to wait before retrying, honoring Discord's rate limit hint."""
    if error.code == 429:
        try:
            return min(float(json.loads(error.read())["retry_after"]), 30)
        except (ValueError, KeyError, TypeError):
            pass
    return 2 ** attempt


def post_payload(url, payload, sleep=time.sleep):
    """POST payload to the webhook, retrying rate limits and server errors.

    Returns the HTTP status code on success and raises DiscordMessageError
    otherwise. The webhook URL is never included in error messages.
    """
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "reusable-workflows-library",
        },
        method="POST",
    )
    for attempt in range(SEND_ATTEMPTS):
        last_attempt = attempt == SEND_ATTEMPTS - 1
        try:
            with urllib.request.urlopen(
                request, timeout=REQUEST_TIMEOUT_SECONDS
            ) as response:
                return response.status
        except urllib.error.HTTPError as error:
            retryable = error.code == 429 or error.code >= 500
            if retryable and not last_attempt:
                sleep(retry_delay(error, attempt))
                continue
            body = error.read().decode("utf-8", errors="replace")
            raise DiscordMessageError(
                f"Discord rejected the message with HTTP status "
                f"{error.code}: {body}"
            ) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            if not last_attempt:
                sleep(2 ** attempt)
                continue
            raise DiscordMessageError("Could not reach Discord.") from None
    raise DiscordMessageError("Could not reach Discord.")


def send_message(config, url, dry_run=False):
    """Validate and send config. With dry_run, print the payload instead."""
    validate_webhook_url(url)
    payload = build_payload(config)
    if dry_run:
        print("Dry run: payload is valid and was not sent.")
        print(json.dumps(payload, indent=2))
        return
    status = post_payload(url, payload)
    print(f"Message delivered to Discord (HTTP {status}).")


def config_from_env(env):
    """Build a MessageConfig from the workflow's environment variables."""
    return MessageConfig(
        message=env.get("MESSAGE", ""),
        username=env.get("USERNAME", ""),
        avatar_url=env.get("AVATAR_URL", ""),
        embed_title=env.get("EMBED_TITLE", ""),
        embed_description=env.get("EMBED_DESCRIPTION", ""),
        embed_url=env.get("EMBED_URL", ""),
        embed_color=env.get("EMBED_COLOR", ""),
        embed_footer=env.get("EMBED_FOOTER", ""),
        embed_timestamp=env.get("EMBED_TIMESTAMP", "") == "true",
        embed_fields=env.get("EMBED_FIELDS", ""),
    )


def run(config, env):
    """Send config using the webhook and dry-run settings in env.

    Masks the webhook URL, reports failures as workflow errors, and returns
    the process exit code.
    """
    url = env.get("WEBHOOK_URL", "")
    if url:
        print(f"::add-mask::{url}")
    try:
        send_message(config, url, dry_run=env.get("DRY_RUN", "") == "true")
    except DiscordMessageError as error:
        print(f"::error::{error}")
        return 1
    return 0


def main():
    """Entry point used by send-discord-message.yml."""
    return run(config_from_env(os.environ), os.environ)


if __name__ == "__main__":
    sys.exit(main())
