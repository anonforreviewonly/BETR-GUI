# BETR-GUI
This is the project repository for the paper 

**Design and Evaluation of an Assisted Programming Interface for Behavior Trees in Robotics**

submitted to IEEE Transactions on Automation Science and Engineering (T-ASE), 2026

This repository is temporary for the anonymized review and will be replaced for the final version.

## Installation instructions
Create a project folder, clone this repo and install requirements
```
git clone https://github.com/anonforreviewonly/BETR-GUI/
```

A slightly adapted version of hypermapper needed:
```
git clone https://github.com/anonforreviewonly/hypermapper/tree/hypermapper-v3
cd hypermapper
pip install -e .
cd ..
```

Py_trees:
```
git clone https://github.com/splintered-reality/py_trees
cd py_trees
pip install -e .
```
Install graphviz: https://graphviz.org/download/

### Install any missing requirements
pip install -r requirements.txt

The requirements file above is based on a pip freeze from the environment used for the experiments.
