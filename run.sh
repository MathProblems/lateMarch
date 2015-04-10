#!/bin/bash

python3 mktraindata.py a
python3 build_classifiers.py data/4.7.a
python3 mktraindata.py s
python3 build_classifiers.py data/4.7.s
python3 mktraindata.py m
python3 build_classifiers.py data/4.7.m
python3 mktraindata.py d
python3 build_classifiers.py data/4.7.d
