#!/bin/bash
#
# Set project version in appropriate places
#

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    exit 1
fi

echo "Setting version to $1 in snap/snapcraft.yaml and setup.py"
sed "s/version: .*/version: \"$1\"/g" -i snap/snapcraft.yaml
sed "s/version=.*,/version=\"$1\",/g" -i setup.py
