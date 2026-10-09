#!/usr/bin/env bash
# Fixed V4 numbers x context presence; existing weights only.
set -euo pipefail
cd /data/coding/scientific-evidence-learning
PYTHON_BIN=${EVIDENCE_PYTHON:-/data/miniconda/envs/torch/bin/python}
DATASET=artifacts/server-dataset-with-difficulty-v1
MODEL_DIR=/data/coding/models/Qwen3-14B
ADAPTER=checkpoints/qwen3-14b-uniform-s41/adapter
RUN_TAG=${EVIDENCE_V5_TAG:-v5}
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
if [[ ! "$RUN_TAG" =~ ^[a-zA-Z0-9_-]+$ ]] || [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Check EVIDENCE_V5_TAG and EVIDENCE_PYTHON." >&2
  exit 2
fi

run_logged() {
  local label=$1
  shift
  mkdir -p logs
  local logfile="logs/${label}.log"
  (set -o noclobber; : > "$logfile") || {
    echo "Log exists. Keep prior evidence and use a new EVIDENCE_V5_TAG." >&2
    return 2
  }
  "$@" 2>&1 | tee "$logfile"
}

control_model() {
  local name=$1 stage=$2
  shift 2
  local extra=()
  if [[ "$name" == uniform ]]; then extra=(--adapter "$ADAPTER"); fi
  run_logged "qwen3-14b-${name}-context-${stage}-${RUN_TAG}" \
    "$PYTHON_BIN" run_v5.py run --dataset "$DATASET" --model "$MODEL_DIR" \
    "${extra[@]}" --source "artifacts/qwen3-14b-${name}-factorial-validation-v4" \
    --out "artifacts/qwen3-14b-${name}-context-${stage}-${RUN_TAG}" "$@"
}

smoke_gate() {
  "$PYTHON_BIN" run_v5.py gate --runs \
    "artifacts/qwen3-14b-base-context-smoke-${RUN_TAG}" \
    "artifacts/qwen3-14b-uniform-context-smoke-${RUN_TAG}"
}

case "${1:-help}" in
  check)
    "$PYTHON_BIN" run.py verify --dataset "$DATASET"
    "$PYTHON_BIN" -m unittest discover -s tests -p 'test_v[2345].py' -v
    bash -n scripts/run_next_v5.sh
    for name in base uniform; do
      extra=()
      if [[ "$name" == uniform ]]; then extra=(--adapter "$ADAPTER"); fi
      "$PYTHON_BIN" run_v5.py plan --dataset "$DATASET" --model "$MODEL_DIR" \
        "${extra[@]}" --source "artifacts/qwen3-14b-${name}-factorial-validation-v4"
    done
    ;;
  smoke|controls)
    mkdir -p logs
    exec 9>logs/v3-gpu.lock
    flock -n 9 || { echo "Another V3/V4/V5 GPU stage holds the lock." >&2; exit 2; }
    if [[ "$1" == smoke ]]; then
      for name in base uniform; do control_model "$name" smoke --limit-blocks 4; done
      smoke_gate
    else
      smoke_gate
      for name in base uniform; do control_model "$name" validation; done
    fi
    ;;
  verify)
    for name in base uniform; do
      "$PYTHON_BIN" run_v5.py verify --run "artifacts/qwen3-14b-${name}-context-validation-${RUN_TAG}"
    done
    ;;
  all)
    bash scripts/run_next_v5.sh check
    bash scripts/run_next_v5.sh smoke
    bash scripts/run_next_v5.sh controls
    bash scripts/run_next_v5.sh verify
    ;;
  *)
    echo "Usage: bash scripts/run_next_v5.sh {check|smoke|controls|verify|all}"
    echo "all runs every stage sequentially and stops on error. No training."
    echo "Full run: 10560 paired attempts; 10544 actual new calls; 16 logged upstream failures."
    ;;
esac
