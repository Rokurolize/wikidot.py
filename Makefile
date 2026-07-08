FORMAT_DIR = src tests

release_from-develop: check-version
	set -e; \
	pr_url=$$(gh pr create --base main --head develop --title "Release v$(version)" --body "Release v$(version)"); \
	gh pr merge --auto --merge "$$pr_url"; \
	for attempt in $$(seq 1 120); do \
		state=$$(gh pr view "$$pr_url" --json state --jq .state); \
		if [ "$$state" = "MERGED" ]; then \
			break; \
		fi; \
		if [ "$$state" = "CLOSED" ]; then \
			echo "Release PR closed before merge: $$pr_url"; \
			exit 1; \
		fi; \
		sleep 30; \
	done; \
	state=$$(gh pr view "$$pr_url" --json state --jq .state); \
	if [ "$$state" != "MERGED" ]; then \
		echo "Release PR did not merge before timeout: $$pr_url"; \
		exit 1; \
	fi; \
	target=$$(gh pr view "$$pr_url" --json mergeCommit --jq '.mergeCommit.oid // empty'); \
	if [ -z "$$target" ]; then \
		echo "Release PR merged without a resolvable merge commit: $$pr_url"; \
		exit 1; \
	fi; \
	gh release create $(version) --target "$$target" --latest --generate-notes --title "$(version)"

build:
	rm -rf dist
	uv build

update-version: check-version
	@echo "Updating version to $(version)"
	@grep -Eq '^version = ".+"' pyproject.toml || (echo "pyproject.toml version field not found"; exit 1)
	@grep -Eq '^__version__ = ".+"' src/wikidot/__init__.py || (echo "src/wikidot/__init__.py __version__ field not found"; exit 1)
	@sed -i.bak 's/^version = ".*"/version = "$(version)"/' pyproject.toml && rm pyproject.toml.bak
	@sed -i.bak 's/__version__ = ".*"/__version__ = "$(version)"/' src/wikidot/__init__.py && rm src/wikidot/__init__.py.bak
	@grep -Fx 'version = "$(version)"' pyproject.toml >/dev/null || (echo "pyproject.toml version was not updated"; exit 1)
	@grep -Fx '__version__ = "$(version)"' src/wikidot/__init__.py >/dev/null || (echo "src/wikidot/__init__.py __version__ was not updated"; exit 1)
	@echo "Version updated in pyproject.toml and src/wikidot/__init__.py"

release: check-version
	echo "Releasing version $(version)"
	make check-clean-worktree
	make update-version version=$(version)
	make format
	make lint-fix
	@if git diff --name-only -- . ':!pyproject.toml' ':!src/wikidot/__init__.py' | grep .; then \
		echo "Unexpected release changes found; review and commit them before releasing."; \
		exit 1; \
	fi
	@if git diff -U0 -- src/wikidot/__init__.py | awk '/^[-+]/ && $$0 !~ /^(---|\+\+\+|[-+]__version__ = ")/ { found=1 } END { exit found ? 0 : 1 }'; then \
		echo "Unexpected non-version changes found in src/wikidot/__init__.py."; \
		exit 1; \
	fi
	git add pyproject.toml src/wikidot/__init__.py
	git commit -m 'release: $(version)' --allow-empty
	git push origin develop
	make release_from-develop version=$(version)

check-clean-worktree:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Worktree must be clean before release."; \
		git status --short; \
		exit 1; \
	fi

check-version:
	@if [ -z "$(strip $(version))" ]; then \
		echo "version is required, for example: make release version=4.4.2"; \
		exit 1; \
	fi
	@if ! printf '%s\n' "$(version)" | grep -Eq '^[0-9][0-9A-Za-z.!+_-]*$$'; then \
		echo "version must be a package version such as 4.4.2, not '$(version)'"; \
		exit 1; \
	fi

commit: export message := $(message)
commit:
	@if [ -z "$$message" ]; then \
		echo "message is required, for example: make commit message='your message'"; \
		exit 1; \
	fi
	make format
	git add .
	git commit -m "$$message"

format:
	uv sync --extra format
	uv run ruff format $(FORMAT_DIR)

format-check:
	uv sync --extra format
	uv run ruff format --check $(FORMAT_DIR)

lint:
	uv sync --extra lint
	uv run ruff check $(FORMAT_DIR)
	uv run mypy $(FORMAT_DIR) --install-types --non-interactive

lint-fix:
	uv sync --extra lint
	uv run ruff check $(FORMAT_DIR) --fix

typecheck:
	uv sync --extra typecheck
	uv run pyright

# テスト関連のコマンド（デフォルトはユニットテストのみ）
test:
	uv sync --extra test
	uv run pytest tests/unit/ -v

test-cov:
	uv sync --extra test
	uv run pytest tests/unit/ -v --cov=src/wikidot --cov-report=term-missing --cov-report=html --cov-report=xml:coverage.xml --cov-fail-under=80 --junitxml=junit.xml -o junit_family=legacy

test-unit:
	uv sync --extra test
	uv run pytest tests/unit/ -v

test-unit-cov:
	uv sync --extra test
	uv run pytest tests/unit/ -v --cov=src/wikidot --cov-report=term-missing --cov-report=html --cov-report=xml:coverage.xml --cov-fail-under=80 --junitxml=junit.xml -o junit_family=legacy

test-integration:
	uv sync --extra test
	uv run pytest tests/integration/ -v

test-integration-cov:
	uv sync --extra test
	uv run pytest tests/integration/ -v --cov=src/wikidot --cov-report=term-missing --cov-report=html --cov-fail-under=50

.PHONY: build release release_from-develop update-version check-clean-worktree check-version format format-check commit lint lint-fix typecheck test test-cov test-unit test-unit-cov test-integration test-integration-cov
