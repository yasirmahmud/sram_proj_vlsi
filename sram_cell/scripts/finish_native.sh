#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/local_env.sh
ocean -nograph -nocdsinit -restore scripts/netlist.ocn -log results/ocean.log > results/ocean.stdout 2>&1
