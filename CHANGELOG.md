# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- Remove `release.yml` from the reusable workflows. It is now an internal workflow and is no longer callable from other repositories. Use `publish-release.yml` to create releases from other repositories.

## [1.4.1] - 2026-09-30

### Changed
- Bump `github/codeql-action/upload-sarif` from `4.38.1` to `4.38.2`.

## [1.4.0] - 2026-09-29

### Added
- Add default labels file `src/labels.json`, including a new `type: ci` label.
- Add `labels-file` and `target-repository` inputs and an optional `access-token` secret to `label-manager.yml`.
- Add npm to the Dependabot configuration.

### Changed
- Reimplement `label-manager.yml` as a self-contained workflow that no longer depends on `outoforbitdev/action-label-manager`.
- `label-manager.yml` now syncs the bundled default labels unless `labels-file` is provided.

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
