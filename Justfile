# Bootstrap: one-time repository initialization
bootstrap:
    pre-commit install

# Install: no external dependencies to install (plain Python stdlib + Docker-based linting)
install:
    @echo "No dependencies to install."

# Test: run the Python unit tests
test:
    python -m unittest discover -s src -p 'test_*.py' -v

# Lint: check code style and formatting via polylint
lint:
    docker run -v $(pwd):/app -v $(pwd)/.linters:/polylint/.linters outoforbitdev/polylint:0.1.0

# Lint-write: polylint 0.1.0 has no documented --fix/write flag (checked
# `docker run outoforbitdev/polylint:0.1.0 --help` and the polylint README,
# which is just a title with no usage docs) — this is a no-op until one exists.
lint-write:
    @echo "polylint has no autofix mode; run 'just lint' and fix findings manually."

# Gate: full verification (test + lint)
gate: test lint
