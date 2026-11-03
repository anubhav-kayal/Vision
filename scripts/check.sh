#!/bin/sh
# Run from the SSD checkout. Remove only generated AppleDouble Python sidecars.
set -eu
cd "$(dirname "$0")/.."
find backend ingestion evaluation migrations -type f -name '._*.py' -exec sh -c '
    for metadata do
        case "$(file -b "$metadata")" in
            AppleDouble*) rm -f "$metadata" ;;
        esac
    done
' sh {} +
mkdir -p .runtime
python_bin="${VISION_PYTHON:-.venv/bin/python}"
PYTHONPATH=. "$python_bin" -m pytest --basetemp="${VISION_TEST_TMP:-.runtime/pytest}" -q
PYTHONPATH=. "$python_bin" -m evaluation.run --top-k 5
PYTHONPATH=. "$python_bin" -m evaluation.diagnostic_run
PYTHONPATH=. "$python_bin" -m evaluation.pilot_run
"$python_bin" -m compileall -q backend ingestion evaluation migrations
git diff --check
