#!/bin/sh

clean=`git status | grep -q "nothing to commit"`
if (( !clean )); then
    git stash -u
fi

poetry build -f wheel

git push upstream
git push upstream v$1
gh release create v$1 --verify-tag --title "Release $1" --notes ""
gh release upload v$1 dist/mapknowledge-$1-py3-none-any.whl

if (( !clean )); then
    git stash pop --quiet
fi
