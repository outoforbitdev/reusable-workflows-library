import unittest

from notify_discord_release import (
    PRERELEASE_COLOR,
    STABLE_COLOR,
    TRUNCATION_NOTICE,
    build_release_config,
    truncate_notes,
)
from send_discord_message import MAX_DESCRIPTION, build_payload

ENV = {
    "VERSION": "1.5.0",
    "RELEASE_URL": "https://github.com/o/r/releases/tag/v1.5.0",
    "RELEASE_NOTES": "### Added\n- thing",
    "REPOSITORY": "o/r",
}


class TestTruncateNotes(unittest.TestCase):
    def test_short_notes_unchanged(self):
        self.assertEqual(truncate_notes("short"), "short")

    def test_long_notes_fit_and_note_the_cut(self):
        result = truncate_notes("x" * 10000)
        self.assertEqual(len(result), MAX_DESCRIPTION)
        self.assertTrue(result.endswith(TRUNCATION_NOTICE))

    def test_exact_limit_unchanged(self):
        notes = "x" * MAX_DESCRIPTION
        self.assertEqual(truncate_notes(notes), notes)


class TestBuildReleaseConfig(unittest.TestCase):
    def test_stable_release(self):
        config = build_release_config(ENV)
        self.assertEqual(config.embed_title, "v1.5.0 released")
        self.assertEqual(config.embed_color, STABLE_COLOR)
        self.assertEqual(config.embed_url, ENV["RELEASE_URL"])
        self.assertEqual(config.embed_footer, "o/r")
        self.assertTrue(config.embed_timestamp)

    def test_prerelease(self):
        config = build_release_config({**ENV, "PRERELEASE": "true"})
        self.assertEqual(config.embed_title, "v1.5.0 released (pre-release)")
        self.assertEqual(config.embed_color, PRERELEASE_COLOR)

    def test_leading_v_is_not_doubled(self):
        config = build_release_config({**ENV, "VERSION": "v1.5.0"})
        self.assertEqual(config.embed_title, "v1.5.0 released")

    def test_produces_valid_payload_with_huge_notes(self):
        env = {**ENV, "RELEASE_NOTES": "x" * 10000}
        payload = build_payload(build_release_config(env))
        self.assertEqual(len(payload["embeds"][0]["description"]), MAX_DESCRIPTION)

    def test_username_and_avatar_passed_through(self):
        config = build_release_config(
            {**ENV, "USERNAME": "Bot", "AVATAR_URL": "https://x/a.png"}
        )
        self.assertEqual(config.username, "Bot")
        self.assertEqual(config.avatar_url, "https://x/a.png")


if __name__ == "__main__":
    unittest.main()
