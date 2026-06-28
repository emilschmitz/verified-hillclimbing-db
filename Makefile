.PHONY: install test test-unit test-slow loop clean

install:
	uv sync

test: test-unit

test-unit:
	uv run pytest transpiler/tests/test_unit.py -v

test-slow:
	RUN_SLOW=1 uv run pytest transpiler/tests/test_functional.py -v

loop:
	uv run python research_loop/harness.py -q 1 --dataset-size 50000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf research_loop/temp_build
