PROJECT := refter-cli
PACKAGE := refter
MODULES := $(wildcard $(PACKAGE)/*.py)

.PHONY: all
all: doctor format check test

VIRTUAL_ENV ?= .venv

.PHONE: venv
venv:
	python -m venv $(VIRTUAL_ENV)


.PHONY: install
install:
	poetry install

.PHONY: clean
clean: ## Delete all generated and temporary files
	find $(PACKAGE) tests -name '__pycache__' -delete
	rm -rf *.egg-info
	rm -rf .cache .pytest .coverage htmlcov
	rm -rf *.spec dist build
	rm -rf $(VIRTUAL_ENV)

test: install
	poetry run pytest $(PACKAGE)

.PHONY: format
format: install
	poetry run isort $(PACKAGE)
	poetry run black $(PACKAGE)

.PHONY: check
check: install format ## Run formaters, linters, and static analysis
ifdef CI
	git diff --exit-code
endif
	poetry run mypy $(PACKAGE)
	poetry run pylint $(PACKAGE) --rcfile=.pylint.ini
	poetry run pydocstyle $(PACKAGE)


DIST_FILES := dist/*.tar.gz dist/*.whl
EXE_FILES := dist/$(PACKAGE).*

.PHONY: dist
dist: install $(DIST_FILES)
$(DIST_FILES): $(MODULES) pyproject.toml
	rm -f $(DIST_FILES)
	poetry build


.PHONY: publish
publish: dist
	git diff --name-only --exit-code
	poetry publish -r refter-cli --build
