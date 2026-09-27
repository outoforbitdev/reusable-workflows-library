# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-09-27

### Changed
- Bump `ossf/scorecard-action` from `2.4.3` to `2.4.4`.
- Bump `github/codeql-action/upload-sarif` from `4.38.0` to `4.38.1`.

## [1.3.0] - 2026-09-17

### Added
- Add `publish-docker.yml`: builds and publishes a Docker image to Docker Hub or GitHub Container Registry, composable as one job in a release chain
- Add `test-docker.yml`: builds a Docker image and runs a test command inside it

## [1.2.0] - 2026-09-17

### Added
- Add a `title` input to `publish-release.yml` so callers can override the release title; defaults to the `v<version>` tag

### Fixed
- Pass `--title` explicitly in `publish-release.yml` so release titles are just the version tag (e.g. `v0.0.4`) instead of falling back to the tag's associated commit message

## [1.1.0] - 2026-09-13

### Added
- Bump [action-label-manager](https://github.com/outoforbitdev/action-label-manager) to `v0.0.3`
- Replace `action-release-changelog` with two composable reusable workflows: `detect-new-changelog-version.yml` and `publish-release.yml`
- Add a `draft` input to `release.yml` so callers can choose draft vs. full releases

## [1.0.0] - 2025-03-15

### Added
- `label-manager.yml`
- `release.yml`
- `scorecard.yml`
