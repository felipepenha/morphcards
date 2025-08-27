# Project Rules

## Basics

- Use Python.

- Make project ready for `pypi` submission as a package, which includes a `pyproject.toml` file.


## Containerization

- Assume `podman` is being used, specially in the docs, in opposition to `docker`. Although compatibility with `docker` is desired.

- Project includes a `Containerfile` that allows for running local experiments and demos with `podman`.

- A `compose.yml` is included when demo requires services.

## Running locally

- Include a `Makefile`.


## Checkers

- Include a way to manually run these in the `Makefile`: `black`, `isort`, `mypy`.


## UI

- Demo is based on a simple `gradio` interface.


## Testing

- Include tests with `pytest` for each new functionality.


## Secrets

- Assume secrets and environment variables are stored in `.env` file. Always make sure `.env` is ignored in `.gitignore`.


## Documentation

- Include thorough technical documentation.

- Include a `mermaid` chart of the project architecture in the docs.


## Git Conventions

- Follow [Semantic Versioning v2.0](https://semver.org/) for version numbering.

- Follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) for the commit messages.
