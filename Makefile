.DEFAULT_GOAL := help

PACKAGE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
VENV := .venv
VENV_BIN := $(VENV)/bin
PYTHON := $(VENV_BIN)/python3
PIP := $(VENV_BIN)/pip
INSTALL_STAMP := $(VENV)/.install.stamp
UPDATE_STAMP := $(VENV)/.update.stamp
DEVELOPER_MODE := 1
COVERAGE_SERVER_PORT := 8000
COVERAGE_DIR := $(PACKAGE_DIR)/build/documentation/coverage/

DEP_FILES := $(wildcard setup.*) $(wildcard requirements*.txt) $(wildcard pyproject.toml)


####################
##@ Helper Commands
####################

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: help

######################
##@ Cleaning Commands
######################


clean-venv:  ## Clean virtualenv
	rm -rf $(VENV)/

clean-install-stamp:
	rm -rf $(INSTALL_STAMP)

clean-build:  ## Clean build artifacts (egg/dist/build etc.) 
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:  ## remove pyc/pyo files 
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

clean-test:  ## Remove test artifacts 
	rm -rf build/.tox/
	rm -rf build/.pytest_cache/

clean-docs:  ## Remove documentation artifacts
	rm -rf build/documentation/
	rm -rf .coverage

clean: clean-install-stamp clean-build clean-pyc clean-test clean-docs ## alias to clean-{build,pyc,test,docs}
obliterate: clean-venv clean  ## alias to clean, clean-venv

.PHONY: clean-venv clean-install-stamp clean-build clean-pyc clean-test clean obliterate


#########################
##@ Installation Commands
#########################

.uv: ## Check that uv is installed
	@uv -V || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: .uv

install: .uv  ## Installs package dependencies
	uv sync --frozen --group all --all-extras

.PHONY: install

rebuild-lockfile: .uv  ## Rebuilds the lockfile
	uv lock --upgrade

.PHONY: rebuild-lockfiles

make install-release: .uv  ## Installs package dependencies
	uv sync --frozen --group release --all-extras
.PHONY: install-release

link-packages: ## Link local packages to virtualenv  
	@parent_dir=$$(dirname $$(pwd)); \
	local_packages=$$(ls $$parent_dir); \
	dependencies=$$(uv pip list --format freeze --exclude-editable | awk -F '==' '{print $$1}');\
	for local_package in $$local_packages; do \
		for dependency in $$dependencies; do \
			if [ $$local_package == $$dependency ]; then \
				echo "Reinstalling $$local_package dependency to local override"; \
				uv pip install -e $$parent_dir/$$local_package; \
			fi \
		done; \
	done

.PHONY: link-packages

unlink-packages: ## Unlink local packages from virtualenv
	@parent_dir=$$(dirname $$(pwd)); \
	this_package=$$(basename $$(pwd)); \
	local_packages=$$(ls $$parent_dir); \
	dependencies=$$(uv pip list --format freeze --editable | awk -F '==' '{print $$1}');\
	is_found=0; \
	for local_package in $$local_packages; do \
		for dependency in $$dependencies; do \
			if [ $$local_package == $$dependency ] && [ $$local_package != $$this_package ]; then \
				is_found=1; \
			fi; \
		done \
	done; \
	if [ $$is_found == 1 ]; then \
		echo "Found dependencies installed locally, reinstalling..."; \
		make install; \
	fi

.PHONY: .uv install install-release rebuild-lockfile link-packages unlink-packages

#######################
##@ Formatting Commands
#######################

lint-ruff: .uv ## Run ruff checker
	uv run ruff check

lint-mypy: .uv ## Run mypy
	uv run mypy ./

lint: lint-ruff lint-mypy  ## Run all lint targets (ruff, mypy)


format-ruff: .uv ## Run ruff formatter 
	uv run ruff check --fix
	uv run ruff format

format: format-ruff  ## Run all formatters (ruff) 

.PHONY: lint-ruff lint-mypy lint format-ruff format-mypy format

#####################
##@ Testing Commands
#####################

pytest: install  ## Run test (pytest)
	uv run pytest -vv --durations=10

test: pytest  ## Run Standard Tests

.PHONY: pytest test

#####################
##@ Inspect Commands
#####################

coverage-server: $(INSTALL_STAMP) ## Run coverage server
	$(PYTHON) -m http.server $(COVERAGE_SERVER_PORT) -d $(COVERAGE_DIR)

.PHONY: coverage-server

#####################
##@ Release Commands
#####################

dist: install-release ## Build source and wheel package
	uv build

reinstall: obliterate install ## Recreate environment and install

pre-build: obliterate ## Removes existing build environment
build: install ## Runs installation
post-build: lint test  ## Run linters and tests   
release: pre-build build post-build  ## Runs pre-build, build, post-build
run: release

.PHONY: dist reinstall pre-build build post-build release run

