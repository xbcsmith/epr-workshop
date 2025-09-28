#!/usr/bin/env bash

echo "Generating slides.md from all .md files (excluding README.md, content, troubleshooting, resources, glossary)..."

rm -vf slides.md

FILES=$(find . -type f -name "*.md" | grep -v README.md | grep -v "content" | grep -v "troubleshooting" | grep -v "resources" | grep -v "glossary" | sort)

cat $FILES > slides.md

echo "Slides generated in slides.md"

echo "Display using 'slides slides.md'" 