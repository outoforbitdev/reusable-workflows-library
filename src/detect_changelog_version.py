import json
import os
import re
import subprocess
import sys
import uuid

VERSION_HEADING_PATTERN = re.compile(
    r'^(#{1,6})\s+(v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)\b'
)
HEADING_PATTERN = re.compile(r'^(#{1,6})\s')
PRERELEASE_SUFFIX_PATTERN = re.compile(r'-[0-9A-Za-z.-]+$')


def parse_changelog(text):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        match = VERSION_HEADING_PATTERN.match(line.strip())
        if not match:
            continue
        heading_level = len(match.group(1))
        version = match.group(2)
        notes_lines = []
        for next_line in lines[i + 1:]:
            # Check if it's a version heading first (stop at any version heading)
            version_match = VERSION_HEADING_PATTERN.match(next_line.strip())
            if version_match:
                break

            # Check if it's a non-version heading at the same level or higher
            heading_match = HEADING_PATTERN.match(next_line.strip())
            if heading_match and len(heading_match.group(1)) <= heading_level:
                break

            notes_lines.append(next_line)
        notes = "\n".join(notes_lines).strip("\n")
        return version, notes
    return None, None


def is_prerelease_version(version):
    stripped = version.split("+", 1)[0]
    return bool(PRERELEASE_SUFFIX_PATTERN.search(stripped))


def normalize_version(version):
    return re.sub(r'^[vV]', '', version)


def get_last_release_tag(releases):
    if not releases:
        return None
    latest = max(releases, key=lambda release: release["created_at"])
    return latest["tag_name"]


def fetch_releases(repo):
    result = subprocess.run(
        [
            "gh", "api", f"repos/{repo}/releases",
            "--paginate", "--jq", ".[] | {tag_name, created_at}",
        ],
        capture_output=True, text=True, check=True,
    )
    return [
        json.loads(line)
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def write_github_output(path, name, value):
    delimiter = f"GHADELIMITER_{uuid.uuid4().hex}"
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def detect(changelog_path, repo):
    with open(changelog_path, encoding="utf-8") as f:
        text = f.read()

    version, notes = parse_changelog(text)
    if version is None:
        print(f"No version heading found in {changelog_path}", file=sys.stderr)
        sys.exit(1)

    releases = fetch_releases(repo)
    previous_tag = get_last_release_tag(releases)
    previous_version = normalize_version(previous_tag) if previous_tag else ""
    new_version = normalize_version(version)

    return {
        "should-release": "true" if new_version != previous_version else "false",
        "new-version": new_version,
        "previous-version": previous_version,
        "release-notes": notes,
        "is-prerelease": "true" if is_prerelease_version(version) else "false",
    }


if __name__ == "__main__":
    changelog_path = sys.argv[1]
    repo = os.environ["GITHUB_REPOSITORY"]
    outputs = detect(changelog_path, repo)
    output_file = os.environ["GITHUB_OUTPUT"]
    for name, value in outputs.items():
        write_github_output(output_file, name, value)
