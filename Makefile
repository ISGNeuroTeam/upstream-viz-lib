.SILENT:

SHELL = /bin/bash


.PHONY: clean clean_dist clean_venv_dev clean_conda

VERSION := $(shell cat setup.py | grep version | head -n 1 | sed -re "s/[^\"']+//" | sed -re "s/[\"',]//g")
BRANCH := $(shell git name-rev $$(git rev-parse HEAD) | cut -d\  -f2 | sed -re 's/^(remotes\/)?origin\///' | tr '/' '_')

CONDA = conda/miniconda/bin/conda
ENV_PYTHON = venv_dev/bin/python3.9


all:
	echo -e "Required section:\n\
 publish - build library archive\n\
 clean - clean all addition file, virtual environment directory, output archive file\n\
 test - run all tests\n\
 dev - deploy project for develop\n\
Addition section:\n\
 venv_dev -  create python virtual environment for develop \n\
 conda/miniconda - install miniconda in local directory \n\
"
conda/miniconda.sh:
	echo Download Miniconda
	mkdir -p conda
	wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.11.0-Linux-x86_64.sh -O conda/miniconda.sh; \

conda/miniconda: conda/miniconda.sh
	bash conda/miniconda.sh -b -p conda/miniconda; \

clean_conda:
	rm -rf ./conda

venv_dev: conda/miniconda
	echo Create environment
	$(CONDA) create --copy -p venv_dev -y
	$(CONDA) install -p venv_dev python==3.9.7 -y
	$(ENV_PYTHON) -m pip install --no-input -r ./requirements.txt  --extra-index-url http://s.dev.isgneuro.com/repository/ot.platform/simple --trusted-host s.dev.isgneuro.com
	$(ENV_PYTHON) -m pip install --no-input -r ./pp_exec_env_requirements.txt --extra-index-url http://s.dev.isgneuro.com/repository/ot.platform/simple --trusted-host s.dev.isgneuro.com

clean_venv_dev:
	rm -rf ./venv_dev

test: venv_dev
	echo Run unittests
	export UPSTREAM_VIZ_DATA_CONFIG="upstream_viz_lib/get_data.yaml"; export UPSTREAM_VIZ_CONFIG="upstream_viz_lib/config.yaml"; export PYTHONPATH="./tests/"; $(ENV_PYTHON) -m unittest discover -s ./tests

clean_dist:
	echo Clean dist folders
	rm -rf upstream_viz_lib.egg-info
	rm -rf build
	rm -rf dist


dev: venv_dev

build: venv_dev
	echo Build

publish: build
	./venv_dev/bin/python setup.py sdist

clean: clean_dist clean_venv_dev clean_conda
