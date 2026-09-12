#!/usr/bin/env bash
set -e

# HRL International - HRL X Noise Cancellation
# Automated Verification, Commit & Push Pipeline

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "=================================================================="
echo "⚡ HRL X Noise Cancellation — Automated Pipeline"
echo "=================================================================="

# 1. Run automated verification suite
echo "🔍 Running Automated Unit & DSP Integrity Suite..."
PYTHONPATH="$REPO_DIR" python3 -m unittest discover -s "$REPO_DIR/tests" -p "test_*.py" -v
if [ $? -ne 0 ]; then
    echo "❌ DSP integrity tests failed. Aborting."
    exit 1
fi
echo "✅ All tests passed."

# 2. Run DSP demo benchmark
echo "📊 Running DSP Synthetic Benchmark..."
PYTHONPATH="$REPO_DIR" python3 -m hrl_noise_cancellation demo

# 3. Check git changes
STATUS=$(GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git status --porcelain)

if [ -n "$STATUS" ]; then
    echo "📦 Staging workspace modifications..."
    GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git add -A

    COMMIT_MSG="$1"
    if [ -z "$COMMIT_MSG" ]; then
        TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
        COMMIT_MSG="chore(auto-sync): synchronized HRL X Noise Cancellation ($TIMESTAMP)"
    fi

    echo "✍️  Creating commit: $COMMIT_MSG"
    GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git -c user.name="hrlpavan" -c user.email="pavankcet@gmail.com" commit -m "$COMMIT_MSG"
else
    echo "ℹ️  Working tree clean. Nothing to commit."
fi

# 4. Check if remote origin exists and push
if GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git remote | grep -q "origin"; then
    echo "🚀 Pushing commits to origin main..."
    GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git push origin main || echo "⚠️  Push requires remote credentials/setup."
fi

echo "=================================================================="
echo "✅ Auto Pipeline Completed Successfully!"
echo "=================================================================="
