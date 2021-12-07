# Lets us source venv a single time
.ONESHELL:

# define the name of the virtual environment directory
VENV := .venv

# default target, when make executed without arguments
.PHONY: all
all: venv

.PHONY: venv
venv:
	python -m venv $(VENV);
	. $(VENV)/bin/activate;
	which python;

.PHONY: build
build: venv
	python setup.py build;

.PHONY: install
install: build
	python setup.py install;

.PHONY: test
test: install
	python setup.py pytest;

.PHONY: clean
clean:
	python setup.py clean
	rm -rf -- $(VENV);
	rm -rf -- ./build ./dist ./.eggs ./.pytest_cache
	find . -type f -name '*.pyc' -delete;
	find . -type d -name '__pycache__' -delete;
	find . -type d -name '*.egg-info' -execdir rm -rf -- '{}' \; ;
	