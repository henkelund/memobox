#!/bin/bash
curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py | sudo python2.7
pip install pwinty
pip install fabric
pip install flask-assets
