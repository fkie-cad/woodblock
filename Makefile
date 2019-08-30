WOODBLOCK_VERSION := 0.1.4

default: tests


.PHONY: init
init:
	pip install -r requirements.txt -U


.PHONY: package
package:
	python setup.py sdist bdist_wheel


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
	@PYTHONPATH=. py.test tests/system


.PHONY: unit-tests
unit-tests:
	@PYTHONPATH=. py.test tests/unit


.PHONY: slow-unit-tests
slow-unit-tests:
	@PYTHONPATH=. py.test --run-slow -m slow tests/unit


.PHONY: bandit
bandit:
	@bandit -r woodblock


.PHONY: cov-report
cov-report:
	@coverage report --rcfile=coverage.ini


.PHONY: pylint
pylint:
	@pylint --rcfile=pylintrc woodblock


.PHONY: version-update
version-update:
	@sed -i -r "s/(.*version=').*/\1$(WOODBLOCK_VERSION)',/" setup.py
	@sed -i -r "s/release .*/release = '$(WOODBLOCK_VERSION)'/" docs/conf.py


.PHONY: clear-test-output
clear-test-output:
	@$(RM) -f .coverage
