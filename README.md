# reusable-workflows-library

A library of reusable workflows.

<p>
  <a href="https://github.com/outoforbitdev/reusable-workflows-library/actions?query=workflow%3ATest+branch%3Amaster">
    <img alt="Test build states" src="https://github.com/outoforbitdev/reusable-workflows-library/workflows/Test/badge.svg">
  </a>
  <a href="https://github.com/outoforbitdev/reusable-workflows-library/actions?query=workflow%3ATest+branch%3Amaster">
    <img alt="Release build states" src="https://github.com/outoforbitdev/reusable-workflows-library/workflows/NPM Publish/badge.svg">
  </a>
  <a href="https://securityscorecards.dev/viewer/?uri=github.com/outoforbitdev/reusable-workflows-library">
    <img alt="OpenSSF Scorecard" src="https://api.securityscorecards.dev/projects/github.com/outoforbitdev/reusable-workflows-library/badge">
  </a>
  <a href="https://github.com/outoforbitdev/reusable-workflows-library/releases/latest">
    <img alt="Latest github release" src="https://img.shields.io/github/v/release/outoforbitdev/reusable-workflows-library?logo=github">
  </a>
  <a href="https://github.com/outoforbitdev/reusable-workflows-library/issues">
    <img alt="Open issues" src="https://img.shields.io/github/issues/outoforbitdev/reusable-workflows-library?logo=github">
  </a>
</p>

## Workflows

### label-manager.yml

Runs [action-label-manager](https://github.com/outoforbitdev/action-label-manager)

#### Example usage

```yml
name: Sync Labels
on:
  issues: 
    types:
      - opened
      - labeled
  pull_request:
    types:
      - opened
      - labeled

# Declare default permissions as read only.
permissions: read-all

jobs:
  labels:
    uses: outoforbitdev/reusable-workflows-library/.github/workflows/label-manager.yml@1.0.0
    permissions:
      issues: write
```

### detect-new-changelog-version.yml

Detects whether the top entry in a changelog file represents a version that
hasn't been released on GitHub yet, and extracts its release notes.

#### Example usage

```yml
jobs:
  detect:
    uses: outoforbitdev/reusable-workflows-library/.github/workflows/detect-new-changelog-version.yml@1.0.0
    with:
      changelog-file: ./CHANGELOG.md
  build-and-publish:
    needs: detect
    if: needs.detect.outputs.should-release == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Releasing ${{ needs.detect.outputs.new-version }}"
```

### publish-release.yml

Creates a GitHub release for a given version, optionally attaching a
previously uploaded workflow artifact.

#### Example usage

```yml
name: Release
on:
  push:
    branches: ["main"]

# Declare default permissions as read only.
permissions: read-all

jobs:
  publish:
    uses: outoforbitdev/reusable-workflows-library/.github/workflows/publish-release.yml@1.0.0
    with:
      version: "1.2.0"
      release-notes: "### Features\n- something new"
    permissions:
      contents: write
```

### release.yml

Detects whether a new version is ready to release (via `detect-new-changelog-version.yml`) and, if so, creates the GitHub release (via `publish-release.yml`).

#### Example usage

```yml
name: Release
on:
  push:
    branches: ["main"]

# Declare default permissions as read only.
permissions: read-all

jobs:
  release:
    uses: outoforbitdev/reusable-workflows-library/.github/workflows/release.yml@1.0.0
    with:
      draft: false
    permissions:
      contents: write
```

### scorecard.yml

Runs [OSSF Scorecard action](https://github.com/ossf/scorecard-action#installation)

#### Example usage

```yml
name: Update OSSF Scorecard
on:
  # For Branch-Protection check. Only the default branch is supported. See
  # https://github.com/ossf/scorecard/blob/main/docs/checks.md#branch-protection
  branch_protection_rule:
  # To guarantee Maintained check is occasionally updated. See
  # https://github.com/ossf/scorecard/blob/main/docs/checks.md#maintained
  schedule:
    - cron: "42 7 * * 4"
  push:
    branches: ["main"]

# Declare default permissions as read only.
permissions: read-all

jobs:
  scorecard:
    uses: outoforbitdev/reusable-workflows-library/.github/workflows/scorecard.yml@1.0.0
    permissions:
      # Needed to upload the results to code-scanning dashboard.
      security-events: write
      # Needed to publish results and get a badge (see publish_results below).
      id-token: write
```
