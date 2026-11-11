"""Announce a release in Discord as an embed.

Used by the notify-discord-release.yml reusable workflow. It formats release
details into an embed and sends it with send_discord_message.
"""

import os
import sys

from send_discord_message import MAX_DESCRIPTION, MessageConfig, run

STABLE_COLOR = "2ea44f"
PRERELEASE_COLOR = "f0883e"
TRUNCATION_NOTICE = "\n\n...see the release for the full notes."


def truncate_notes(notes, limit=MAX_DESCRIPTION):
    """Shorten notes to fit an embed description, noting the cut."""
    if len(notes) <= limit:
        return notes
    keep = limit - len(TRUNCATION_NOTICE)
    return notes[:keep].rstrip() + TRUNCATION_NOTICE


def build_release_config(env):
    """Build the embed MessageConfig for a release from env variables."""
    prerelease = env.get("PRERELEASE", "") == "true"
    version = env.get("VERSION", "").lstrip("v")
    suffix = " (pre-release)" if prerelease else ""
    return MessageConfig(
        username=env.get("USERNAME", ""),
        avatar_url=env.get("AVATAR_URL", ""),
        embed_title=f"v{version} released{suffix}",
        embed_url=env.get("RELEASE_URL", ""),
        embed_description=truncate_notes(env.get("RELEASE_NOTES", "")),
        embed_color=PRERELEASE_COLOR if prerelease else STABLE_COLOR,
        embed_footer=env.get("REPOSITORY", ""),
        embed_timestamp=True,
    )


def main():
    """Entry point used by notify-discord-release.yml."""
    return run(build_release_config(os.environ), os.environ)


if __name__ == "__main__":
    sys.exit(main())
