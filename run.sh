#!/bin/bash

python3 mktraindata.py as
python3 mktraindata.py asmd
python3 mktraindata.py md
python3 build_classifiers.py data/3.19.as
python3 build_classifiers.py data/3.19.asmd
python3 build_classifiers.py data/3.19.md
