.RECIPEPREFIX = >
.PHONY: setup data validate test clean

setup:
> uv sync --frozen

data:
> uv run python -m optlab.ingest.run --config conf/settings.yaml

validate:
> uv run python -m optlab.validate.run --config conf/settings.yaml

test:
> uv run python -m pytest tests -q

clean:
> rm -rf data/cache/*
