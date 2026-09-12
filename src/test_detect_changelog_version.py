import unittest

from detect_changelog_version import (  # noqa: F811 (re-import with additions)
    get_last_release_tag,
    is_prerelease_version,
    normalize_version,
    parse_changelog,
)


class TestParseChangelog(unittest.TestCase):
    def test_skips_document_title_heading(self):
        text = "# Changelog\n\n## 1.2.0\n\nSome notes.\n"
        version, notes = parse_changelog(text)
        self.assertEqual(version, "1.2.0")
        self.assertEqual(notes, "Some notes.")

    def test_skips_placeholder_heading_above_real_version(self):
        text = (
            "# Changelog\n\n"
            "## Next Release\n\n"
            "- some change being drafted\n\n"
            "## 1.1.0\n\n"
            "### Features\n"
            "- a shipped feature\n"
        )
        version, notes = parse_changelog(text)
        self.assertEqual(version, "1.1.0")
        self.assertEqual(notes, "### Features\n- a shipped feature")

    def test_handles_v_prefix_and_trailing_date(self):
        text = "## v1.2.0 (2026-08-12)\n\nNotes here.\n"
        version, notes = parse_changelog(text)
        self.assertEqual(version, "v1.2.0")
        self.assertEqual(notes, "Notes here.")

    def test_stops_notes_at_next_heading_of_same_level(self):
        text = "## 1.2.0\n\nNotes for 1.2.0.\n\n## 1.1.0\n\nNotes for 1.1.0.\n"
        version, notes = parse_changelog(text)
        self.assertEqual(version, "1.2.0")
        self.assertEqual(notes, "Notes for 1.2.0.")

    def test_preserves_nested_subheadings_as_notes_content(self):
        text = (
            "## 1.1.0\n\n"
            "### Features\n"
            "- feature one\n\n"
            "### Bug Fixes\n"
            "- fix one\n\n"
            "## 1.0.0\n\n"
            "first release\n"
        )
        version, notes = parse_changelog(text)
        self.assertEqual(version, "1.1.0")
        self.assertEqual(
            notes,
            "### Features\n- feature one\n\n### Bug Fixes\n- fix one",
        )

    def test_handles_inconsistent_heading_levels_between_entries(self):
        text = "# 2.0.0\n\nBig release.\n\n## 1.0.0\n\nFirst release.\n"
        version, notes = parse_changelog(text)
        self.assertEqual(version, "2.0.0")
        self.assertEqual(notes, "Big release.")

    def test_returns_none_when_no_version_heading_exists(self):
        text = "# Changelog\n\n## Unreleased\n\n- work in progress\n"
        version, notes = parse_changelog(text)
        self.assertIsNone(version)
        self.assertIsNone(notes)


class TestIsPrereleaseVersion(unittest.TestCase):
    def test_true_for_prerelease_suffix(self):
        self.assertTrue(is_prerelease_version("1.0.0-beta.1"))

    def test_false_for_plain_version(self):
        self.assertFalse(is_prerelease_version("1.0.0"))


class TestNormalizeVersion(unittest.TestCase):
    def test_strips_leading_v(self):
        self.assertEqual(normalize_version("v1.2.0"), "1.2.0")

    def test_leaves_unprefixed_version_unchanged(self):
        self.assertEqual(normalize_version("1.2.0"), "1.2.0")


class TestGetLastReleaseTag(unittest.TestCase):
    def test_picks_most_recently_created_release(self):
        releases = [
            {"tag_name": "v1.0.0", "created_at": "2026-01-01T00:00:00Z"},
            {"tag_name": "v1.1.0", "created_at": "2026-02-01T00:00:00Z"},
        ]
        self.assertEqual(get_last_release_tag(releases), "v1.1.0")

    def test_considers_draft_releases(self):
        # No `draft` field is inspected at all -- the caller is responsible
        # for including drafts in `releases` in the first place.
        releases = [
            {"tag_name": "v1.1.0", "created_at": "2026-02-01T00:00:00Z"},
        ]
        self.assertEqual(get_last_release_tag(releases), "v1.1.0")

    def test_returns_none_for_empty_list(self):
        self.assertIsNone(get_last_release_tag([]))


if __name__ == "__main__":
    unittest.main()
