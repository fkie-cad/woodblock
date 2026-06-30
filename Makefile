WOODBLOCK_VERSION := 0.1.7

default: tests


.PHONY: init
init:
	pip install -e .[dev] -U


.PHONY: package
package:
	python -m build


.PHONY: upload
upload:
	twine check dist/*
	twine upload --skip-existing dist/*


.PHONY: docs
docs:
	@$(MAKE) -C docs/ html


.PHONY: serve-docs
serve-docs: docs
	@cd docs && sphinx-serve


.PHONY: proselint
proselint:
	@proselint -c docs/*.rst


.PHONY: tests
tests: clear-test-output unit-tests system-tests


.PHONY: all-tests
all-tests: clear-test-output tests slow-unit-tests


.PHONY: system-tests
system-tests:
	@PYTHONPATH=. pytest tests/system


.PHONY: unit-tests
unit-tests:
	@PYTHONPATH=. pytest tests/unit


.PHONY: slow-unit-tests
slow-unit-tests:
	@PYTHONPATH=. pytest --run-slow -m slow tests/unit


.PHONY: bandit
bandit:
	@bandit -r woodblock


.PHONY: cov-report
cov-report:
	@coverage report --rcfile=coverage.ini


.PHONY: ruff
ruff:
	@ruff check woodblock
	@ruff format --check woodblock


.PHONY: format
format:
	@ruff format woodblock
	@ruff check --fix woodblock


.PHONY: version-update
version-update:
	@sed -i -r "s/^version = .*/version = \"$(WOODBLOCK_VERSION)\"/" pyproject.toml
	@sed -i -r "s/release .*/release = '$(WOODBLOCK_VERSION)'/" docs/conf.py


.PHONY: clear-test-output
clear-test-output:
	@$(RM) -f .coverage
