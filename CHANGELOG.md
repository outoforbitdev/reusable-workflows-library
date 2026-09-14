## 1.1.1

### Fixes
- Pass `--title` explicitly in `publish-release.yml` so release titles are just the version tag (e.g. `v0.0.4`) instead of falling back to the tag's associated commit message

## 1.1.0

### Features
- Bump [action-label-manager](https://github.com/outoforbitdev/action-label-manager) to `v0.0.3`
- Replace `action-release-changelog` with two composable reusable workflows: `detect-new-changelog-version.yml` and `publish-release.yml`
- Add a `draft` input to `release.yml` so callers can choose draft vs. full releases

## 1.0.0

### Features

- `label-manager.yml`
- `release.yml`
- `scorecard.yml`