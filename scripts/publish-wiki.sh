#!/usr/bin/env sh
# Publish docs/wiki/*.md to the GitHub Wiki for hefftv/VOD-tags.
#
# Prerequisites:
#   - gh auth login   OR   git credentials for github.com
#   - Wiki enabled: Repository Settings -> Features -> Wikis
#
# Usage:
#   ./scripts/publish-wiki.sh

set -e

REPO="hefftv/VOD-tags"
WIKI_DIR="${WIKI_DIR:-/tmp/vod-tags-wiki}"
DOCS_DIR="$(cd "$(dirname "$0")/../docs/wiki" && pwd)"

echo "Publishing wiki pages from ${DOCS_DIR} ..."

if [ ! -d "${WIKI_DIR}/.git" ]; then
  git clone "https://github.com/${REPO}.wiki.git" "${WIKI_DIR}" 2>/dev/null || {
    echo "Wiki repo does not exist yet. Creating initial wiki..."
    mkdir -p "${WIKI_DIR}"
    cd "${WIKI_DIR}"
    git init
    git remote add origin "https://github.com/${REPO}.wiki.git"
    cp "${DOCS_DIR}"/*.md .
    git add .
    git commit -m "Initial wiki documentation"
    git branch -M master
    git push -u origin master
    echo "Wiki published to https://github.com/${REPO}/wiki"
    exit 0
  }
fi

cp "${DOCS_DIR}"/*.md "${WIKI_DIR}/"
cd "${WIKI_DIR}"

if git diff --quiet; then
  echo "No wiki changes to publish."
  exit 0
fi

git add .
git commit -m "Update documentation from docs/wiki"
git push origin master

echo "Wiki published to https://github.com/${REPO}/wiki"
