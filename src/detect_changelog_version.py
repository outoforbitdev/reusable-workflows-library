import re

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
