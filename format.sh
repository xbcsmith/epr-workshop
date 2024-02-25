#!/usr/bin/env bash

echo "Formatting Markdown files..."
find . -type f -name '*.md' -print0 | xargs -0 -n 1 prettier --write --parser markdown --prose-wrap always
