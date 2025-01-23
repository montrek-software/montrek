#!/bin/bash
find . -name 'requirements.in' -exec pip-compile --output-file=- {} \; >all-requirements.txt
pip-sync all-requirements.txt
rm all-requirements.txt
