# Lets us source venv a single time
.ONESHELL:

# define the name of the virtual environment directory
VENV := ".venv"

# Container info used during testing
CONTAINER_NAME := "emqx_for_testing"
CONTAINER_IMAGE := "emqx/emqx:4.3.7"
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

.PHONY: clean
clean:
	make stop-broker;

	python setup.py clean;
	rm -rf -- $(VENV);
	rm -rf -- ./build ./dist ./.eggs ./.pytest_cache;
	find . -type f -name '*.pyc' -delete;
	find . -type d -name '__pycache__' -delete;
	find . -type d -name '*.egg-info' -execdir rm -rf -- '{}' \; ;

	

.PHONY: start-broker
start-broker:
	@echo "Starting broker"
	
	if [ "$$(docker container inspect -f '{{.State.Status}}' $(CONTAINER_NAME) )" != "running" ]; then \
		docker run --rm --name $(CONTAINER_NAME) -d -e EMQX_LOG__LEVEL=debug -p1883:1883 -p8883:8883 -p8083:8083 -p8084:8084 $(CONTAINER_IMAGE); \
	else \
		echo "Already running"; \
	fi

	until docker logs $(CONTAINER_NAME) | grep "is running now"; do sleep 3; done

.PHONY: stop-broker
stop-broker:
	docker stop $(CONTAINER_NAME)

.PHONY: run-test
run-test:
	python setup.py pytest;

.PHONY: test
test: install start-broker run-test stop-broker

