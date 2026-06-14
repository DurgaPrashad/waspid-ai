#!/bin/bash
# Waspid AI OS
# This hook was installed by Waspid
# It calls the pre-commit script in the .waspid directory

if [ -x ".waspid/pre-commit.sh" ]; then
    source ".waspid/pre-commit.sh"
    exit $?
else
    echo "Warning: .waspid/pre-commit.sh not found or not executable"
    exit 0
fi
