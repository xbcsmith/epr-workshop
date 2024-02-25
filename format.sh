#!/usr/bin/env bash

echo "Formatting Markdown files..."
find . -type f -name '*.md' -print0 | xargs -0 -n 1 prettier --write --parser markdown --prose-wrap always

echo "Fix ordering"
find . -type f -name 'README.md' -print0 | xargs -0 -n 1 sed -i 's/[2-9]. /1. /g'
