#!/usr/bin/env bash
# Output order x alias mapping. New artifacts only; no training or test-set use.
set -euo pipefail
cd /data/coding/scientific-evidence-learning
PYTHON_BIN=${EVIDENCE_PYTHON:-/data/miniconda/envs/torch/bin/python}
MODEL_DIR=/data/coding/models/Qwen3-14B
DATASET=artifacts/server-dataset-with-difficulty-v1
ADAPTER=checkpoints/qwen3-14b-uniform-s41/adapter
RUN_TAG=${EVIDENCE_V4_TAG:-v4}
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
if [[ ! "$RUN_TAG" =~ ^[a-zA-Z0-9_-]+$ ]] || [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Check EVIDENCE_V4_TAG and EVIDENCE_PYTHON." >&2
  exit 2
fi

run_logged() {
  local label=$1
  shift
  mkdir -p logs
  local logfile="logs/${label}.log"
  (set -o noclobber; : > "$logfile") || {
    echo "Log exists. Preserve it and select a new EVIDENCE_V4_TAG." >&2
    return 2
  }
  "$@" 2>&1 | tee "$logfile"
}

control_model() {
  local name=$1 stage=$2
  shift 2
  local extra=()
  if [[ "$name" == uniform ]]; then extra=(--adapter "$ADAPTER"); fi
  run_logged "qwen3-14b-${name}-factorial-${stage}-${RUN_TAG}" \
    "$PYTHON_BIN" run_v4.py run --dataset "$DATASET" --model "$MODEL_DIR" \
    "${extra[@]}" --reference "artifacts/qwen3-14b-${name}-controls-validation-v3" \
    --out "artifacts/qwen3-14b-${name}-factorial-${stage}-${RUN_TAG}" "$@"
}

smoke_gate() {
  "$PYTHON_BIN" run_v4.py gate --runs \
    "artifacts/qwen3-14b-base-factorial-smoke-${RUN_TAG}" \
    "artifacts/qwen3-14b-uniform-factorial-smoke-${RUN_TAG}"
}

case "${1:-help}" in
  check)
    "$PYTHON_BIN" -c 'import sys,torch,transformers,peft; print(sys.executable); print("torch",torch.__version__,"transformers",transformers.__version__,"peft",peft.__version__); assert torch.cuda.is_available()'
    "$PYTHON_BIN" run.py verify --dataset "$DATASET"
    "$PYTHON_BIN" -m unittest discover -s tests -p 'test_v[234].py' -v
    bash -n scripts/run_next_v4.sh
    for name in base uniform; do
      extra=()
      if [[ "$name" == uniform ]]; then extra=(--adapter "$ADAPTER"); fi
      "$PYTHON_BIN" run_v4.py plan --dataset "$DATASET" --model "$MODEL_DIR" \
        "${extra[@]}" --reference "artifacts/qwen3-14b-${name}-controls-validation-v3"
    done
    ;;
  smoke|controls)
    mkdir -p logs
    # Use the existing V3 lock as well so the two entry points cannot overlap.
    exec 9>logs/v3-gpu.lock
    flock -n 9 || { echo "Another V3/V4 stage holds the GPU lock." >&2; exit 2; }
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
      "$PYTHON_BIN" run_v4.py verify \
        --run "artifacts/qwen3-14b-${name}-factorial-validation-${RUN_TAG}"
    done
    ;;
  *)
    echo "Usage: bash scripts/run_next_v4.sh {check|smoke|controls|verify}"
    echo "check/verify: CPU; smoke: 128 model calls; controls: 5280 calls, two models serially."
    ;;
esac
