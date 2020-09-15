# Contributing

## setup your dev env

project is managed by [`poetry`](https://github.com/python-poetry/poetry)

```bash
poetry install
```

## lint

```bash
pre-commit run --all-files
mypy bgmi
flake8 bgmi
```

## test

```bash
pytest --cache-requests
```
