import os
import tempfile
import unittest
from unittest.mock import patch

from detect_changelog_version import (  # noqa: F811 (re-import with additions)
    detect,
    fetch_releases,
    get_last_release_tag,
    is_prerelease_version,
    normalize_version,
    parse_changelog,
    write_github_output,
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


class TestFetchReleases(unittest.TestCase):
    @patch("detect_changelog_version.subprocess.run")
    def test_parses_newline_delimited_json_from_gh(self, mock_run):
        mock_run.return_value.stdout = (
            '{"tag_name": "v1.0.0", "created_at": "2026-01-01T00:00:00Z"}\n'
            '{"tag_name": "v1.1.0", "created_at": "2026-02-01T00:00:00Z"}\n'
        )
        releases = fetch_releases("outoforbitdev/reusable-workflows-library")
        self.assertEqual(
            releases,
            [
                {"tag_name": "v1.0.0", "created_at": "2026-01-01T00:00:00Z"},
                {"tag_name": "v1.1.0", "created_at": "2026-02-01T00:00:00Z"},
            ],
        )
        args = mock_run.call_args.args[0]
        self.assertEqual(args[0], "gh")
        self.assertIn(
            "repos/outoforbitdev/reusable-workflows-library/releases", args
        )
        self.assertIn("--paginate", args)

    @patch("detect_changelog_version.subprocess.run")
    def test_returns_empty_list_when_no_releases_exist(self, mock_run):
        mock_run.return_value.stdout = ""
        self.assertEqual(fetch_releases("outoforbitdev/empty-repo"), [])


class TestWriteGithubOutput(unittest.TestCase):
    def test_writes_multiline_value_with_delimiter(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "github_output")
            open(output_path, "w").close()

            write_github_output(output_path, "release-notes", "line one\nline two")

            with open(output_path) as f:
                content = f.read()

            self.assertIn("release-notes<<", content)
            self.assertIn("line one\nline two", content)
            # The delimiter line must appear both to open and close the block.
            delimiter = content.split("release-notes<<", 1)[1].splitlines()[0]
            self.assertEqual(content.count(delimiter), 2)


class TestDetect(unittest.TestCase):
    @patch("detect_changelog_version.fetch_releases")
    def test_should_release_true_when_versions_differ(self, mock_fetch):
        mock_fetch.return_value = [
            {"tag_name": "v1.0.0", "created_at": "2026-01-01T00:00:00Z"},
        ]
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False
        ) as changelog:
            changelog.write("## 1.1.0\n\n### Features\n- new thing\n")
            changelog_path = changelog.name

        try:
            result = detect(changelog_path, "outoforbitdev/example")
        finally:
            os.remove(changelog_path)

        self.assertEqual(
            result,
            {
                "should-release": "true",
                "new-version": "1.1.0",
                "previous-version": "1.0.0",
                "release-notes": "### Features\n- new thing",
                "is-prerelease": "false",
            },
        )

    @patch("detect_changelog_version.fetch_releases")
    def test_should_release_false_when_already_released(self, mock_fetch):
        mock_fetch.return_value = [
            {"tag_name": "v1.1.0", "created_at": "2026-02-01T00:00:00Z"},
        ]
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False
        ) as changelog:
            changelog.write("## 1.1.0\n\nAlready released.\n")
            changelog_path = changelog.name

        try:
            result = detect(changelog_path, "outoforbitdev/example")
        finally:
            os.remove(changelog_path)

        self.assertEqual(result["should-release"], "false")

    @patch("detect_changelog_version.fetch_releases")
    def test_should_release_false_when_an_older_release_matches(self, mock_fetch):
        # An out-of-order release (e.g. a prerelease cut from `dev` after
        # `main`'s version was released) means the MOST RECENT release tag is
        # not the one matching the changelog's top version -- but that version
        # is already released, so `should-release` must still be false.
        mock_fetch.return_value = [
            {"tag_name": "v1.1.0", "created_at": "2026-02-01T00:00:00Z"},
            {"tag_name": "v1.2.0-beta.1", "created_at": "2026-03-01T00:00:00Z"},
        ]
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False
        ) as changelog:
            changelog.write("## 1.1.0\n\nAlready released.\n")
            changelog_path = changelog.name

        try:
            result = detect(changelog_path, "outoforbitdev/example")
        finally:
            os.remove(changelog_path)

        self.assertEqual(result["should-release"], "false")
        self.assertEqual(result["previous-version"], "1.2.0-beta.1")

    @patch("detect_changelog_version.fetch_releases")
    def test_exits_with_error_when_no_version_found(self, mock_fetch):
        mock_fetch.return_value = []
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False
        ) as changelog:
            changelog.write("# Changelog\n\n## Unreleased\n\n- wip\n")
            changelog_path = changelog.name

        try:
            with self.assertRaises(SystemExit) as ctx:
                detect(changelog_path, "outoforbitdev/example")
            self.assertEqual(ctx.exception.code, 1)
        finally:
            os.remove(changelog_path)


if __name__ == "__main__":
    unittest.main()
