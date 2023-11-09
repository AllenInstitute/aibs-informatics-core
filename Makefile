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

create-venv: $(PYTHON)  ## Creates virtualenv
$(PYTHON):
	python3 -m venv $(VENV) --prompt $(shell basename $(PACKAGE_DIR))
	$(PYTHON) -m pip install --upgrade pip

install: $(INSTALL_STAMP) ## Installs package dependencies
$(INSTALL_STAMP): $(PYTHON) $(DEP_FILES)
	@. $(VENV_BIN)/activate;\
	$(PIP) install -e .[dev]; 
	@touch $(INSTALL_STAMP)

install-force: clean-install-stamp install ## Force install package dependencies

link-packages: ## Link local packages to virtualenv  
	@parent_dir=$$(dirname $$(pwd)); \
	local_packages=$$(ls $$parent_dir); \
	dependencies=$$($(PIP) list --format freeze --exclude-editable | awk -F '==' '{print $$1}');\
	for local_package in $$local_packages; do \
		for dependency in $$dependencies; do \
			if [ $$local_package == $$dependency ]; then \
				echo "Reinstalling $$local_package dependency to local override"; \
				$(PIP) install -e $$parent_dir/$$local_package --no-deps; \
			fi \
		done; \
	done

unlink-packages: ## Unlink local packages from virtualenv
	@parent_dir=$$(dirname $$(pwd)); \
	this_package=$$(basename $$(pwd)); \
	local_packages=$$(ls $$parent_dir); \
	dependencies=$$($(PIP) list --format freeze --editable | awk -F '==' '{print $$1}');\
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
		make clean-install-stamp install; \
	fi

.PHONY: create-venv install install-force link-packages unlink-packages

#######################
##@ Formatting Commands
#######################

lint-black: $(INSTALL_STAMP) ## Run black (check only)
	$(VENV_BIN)/black ./ --check

lint-isort: $(INSTALL_STAMP) ## Run isort (check only) 
	$(VENV_BIN)/isort ./ --check

lint-mypy: $(INSTALL_STAMP) ## Run mypy
	$(VENV_BIN)/mypy ./


lint: lint-isort lint-black lint-mypy  ## Run all lint targets (black, isort, mypy)


format-black: $(INSTALL_STAMP) ## Format code using black
	$(VENV_BIN)/black ./

format-isort: $(INSTALL_STAMP) ## Format code using isort
	$(VENV_BIN)/isort ./


format: format-isort format-black  ## Run all formatters (black, isort) 

.PHONY: lint-isort lint-black lint-mypy lint format-lint format-black format-mypy format

#####################
##@ Testing Commands
#####################

pytest: $(INSTALL_STAMP)  ## Run test (pytest)
	$(VENV_BIN)/pytest -vv --durations=10

tox: $(INSTALL_STAMP)  ## Run Test in tox environment
	$(VENV_BIN)/tox

test: pytest  ## Run Standard Tests

.PHONY: pytest tox test


#####################
##@ Inspect Commands
#####################

coverage-server: $(INSTALL_STAMP) ## Run coverage server
	$(PYTHON) -m http.server $(COVERAGE_SERVER_PORT) -d $(COVERAGE_DIR)


#####################
##@ Release Commands
#####################

reinstall: obliterate install ## Recreate environment and install

pre-build: obliterate ## Removes existing build environment
build: install ## Runs installation
post-build: lint test  ## Run linters and tests   
release: pre-build build post-build  ## Runs pre-build, build, post-build
run: release

.PHONY: reinstall pre-build build post-build release run
