default: tests


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


.PHONY: cov-report
cov-report:
	@coverage report --rcfile=coverage.ini


.PHONY: clear-test-output
clear-test-output:
	@$(RM) -f .coverage
