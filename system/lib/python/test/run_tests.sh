#!/bin/bash
cd "$(dirname ""$0"")"
CWD="$(pwd)"
PYTHONPATH="$PYTHONPATH:$CWD/.."
PYTHON="$(which python)"
export PYTHONPATH
"$PYTHON" -m unittest discover
