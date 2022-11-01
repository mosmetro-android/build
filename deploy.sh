#!/usr/bin/env bash

set -e

[ -e build ] && rm -rf build
git worktree add -f build data

rm -rf build/*
mkdir build/apks

python -m src.build

pushd build
git add .
git commit --amend -m "Initial commit"
git push --force origin data
popd

rm -rf build
git worktree prune
