#!/bin/bash

# Requirements
# python3 -m venv .server_venv
# source .server_venv/bin/activate

pip install -U pip
pip install -r requirements.txt
pip install opencv-python-headless==4.8.1.78

pip install --pre --upgrade ipex-llm[xpu] --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/
