default: tests


.PHONY: init
init:
	pip install -r requirements.txt -U


.PHONY: package
package:
	python setup.py sdist bdist_wheel


.PHONY: upload
upload:
	twine upload --skip-existing dist/*


.PHONY: docs
docs:
	@cd documentation && \
	  docnado --html ../docs/


.PHONY: proselint
proselint:
	@proselint -c documentation/docs/


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


.PHONY: clear-test-output
clear-test-output:
	@$(RM) -f .coverage
