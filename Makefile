default: tests


.PHONY: docs
docs:
	@cd documentation && \
	  docnado --find-orphans && \
	  docnado --html ../docs/


.PHONY: tests
tests: unit-tests system-tests


.PHONY: all-tests
all-tests: tests slow-unit-tests


.PHONY: system-tests
system-tests:
	@PYTHONPATH=. py.test tests/system


.PHONY: unit-tests
unit-tests:
	@PYTHONPATH=. py.test tests/unit


.PHONY: slow-unit-tests
slow-unit-tests:
	@PYTHONPATH=. py.test --run-slow -m slow tests/unit
