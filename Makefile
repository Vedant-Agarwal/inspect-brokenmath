# MANAGED FILE - Updates pulled from template. See MANAGED_FILES.md
PYTHON_MINOR := $(shell uv run python --version 2>&1 | sed 's/Python 3\.\([0-9]*\).*/\1/')
TEST_GROUP_PY311 := test_py311_or_lower
TEST_GROUP_PY312 := test_py312_or_higher
DEFAULT_TEST_GROUP := $(shell [ "$(PYTHON_MINOR)" -le "11" ] && echo "$(TEST_GROUP_PY311)" || echo "$(TEST_GROUP_PY312)")

hooks:
	uv run pre-commit install

check:
	@bash tools/run_checks.sh

TEST_ARGS ?=
TEST_EXTRAS ?= test
TEST_GROUPS ?= $(DEFAULT_TEST_GROUP)
test:
	@echo "PYTHON_MINOR=$(PYTHON_MINOR)"
	@echo "TEST_GROUPS=$(TEST_GROUPS)"
	@echo "TEST_EXTRAS=$(TEST_EXTRAS)"
	GIT_LFS_SKIP_SMUDGE=1 uv run \
		$(addprefix --extra ,$(TEST_EXTRAS)) \
		$(addprefix --group ,$(TEST_GROUPS)) \
		pytest $(TEST_ARGS)

.PHONY: hooks check test
