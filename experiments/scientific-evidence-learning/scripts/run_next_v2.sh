#!/usr/bin/env bash
# Run only the requested stage. No training or model downloading is performed.
set -euo pipefail
cd /data/coding/scientific-evidence-learning

MODEL_DIR=/data/coding/models/Qwen3-14B
DATASET=artifacts/server-dataset-with-difficulty-v1
ADAPTER=checkpoints/qwen3-14b-uniform-s41/adapter
RUN_TAG=${EVIDENCE_V2_TAG:-v2}
if [[ ! "$RUN_TAG" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo "EVIDENCE_V2_TAG must use only letters, digits, underscores and hyphens." >&2
  exit 2
fi

run_logged() {
  local label=$1
  shift
  mkdir -p logs
  if [[ -e "logs/${label}.log" ]]; then
    echo "Log exists: logs/${label}.log. For a new run, set EVIDENCE_V2_TAG to a new value." >&2
    return 2
  fi
  "$@" 2>&1 | tee "logs/${label}.log"
}

diagnose_model() {
  local name=$1
  local stage=$2
  shift 2
  local adapter_args=()
  if [[ "$name" == uniform ]]; then
    adapter_args=(--adapter "$ADAPTER")
  fi
  run_logged "qwen3-14b-${name}-${stage}-${RUN_TAG}" \
    python3 run_v2.py diagnose --dataset "$DATASET" --model "$MODEL_DIR" \
    "${adapter_args[@]}" --device cuda --thinking-mode off \
    --variants canonical shuffled --order-seeds 0 --objectives conditional_max \
    --out "artifacts/qwen3-14b-${name}-${stage}-${RUN_TAG}" "$@"
}

case "${1:-help}" in
  check)
    python3 run.py verify --dataset artifacts/server-dataset-v1
    python3 run.py verify --dataset "$DATASET"
    if python3 -c "import importlib.util; raise SystemExit(importlib.util.find_spec('ruff') is None)"; then
      python3 -m ruff check run_v2.py src/evidence_lab_v2 tests/test_v2.py
    else
      echo "Optional ruff is unavailable; executable regression and data checks remain required."
    fi
    python3 -m unittest discover -s tests -p 'test_v2.py' -v
    bash -n scripts/run_next_v2.sh
    python3 run_v2.py diagnose --dataset "$DATASET" --model "$MODEL_DIR" \
      --out artifacts/preview-readouts-never-written --dry-run
    python3 run_v2.py diagnose --dataset "$DATASET" --model "$MODEL_DIR" --adapter "$ADAPTER" \
      --out artifacts/preview-readouts-smoke-never-written --limit 12 --dry-run
    python3 run_v2.py orders --dataset "$DATASET" --model "$MODEL_DIR" \
      --objectives conditional_max conditional_min \
      --out artifacts/preview-orders-never-written --dry-run
    ;;
  baselines)
    python3 run.py verify --dataset "$DATASET"
    run_logged "e0-rules-test-${RUN_TAG}" python3 run.py rules \
      --dataset "$DATASET" --split test --out "artifacts/e0-rules-test-${RUN_TAG}"
    run_logged "qwen3-14b-e1-test-${RUN_TAG}" python3 run.py evaluate \
      --dataset "$DATASET" --model "$MODEL_DIR" --device cuda --thinking-mode off \
      --split test --out "artifacts/qwen3-14b-e1-test-${RUN_TAG}"
    ;;
  smoke)
    diagnose_model base readouts-smoke --limit 12
    diagnose_model uniform readouts-smoke --limit 12
    ;;
  diagnose)
    diagnose_model base readouts-validation
    diagnose_model uniform readouts-validation
    ;;
  orders)
    for name in base uniform; do
      adapter_args=()
      if [[ "$name" == uniform ]]; then
        adapter_args=(--adapter "$ADAPTER")
      fi
      run_logged "qwen3-14b-${name}-orders-validation-${RUN_TAG}" \
        python3 run_v2.py orders --dataset "$DATASET" --model "$MODEL_DIR" \
        "${adapter_args[@]}" --device cuda --thinking-mode off \
        --objectives conditional_max conditional_min \
        --variants canonical reversed block_shuffled within_block_shuffled shuffled \
        --order-seeds 0 1 2 --out "artifacts/qwen3-14b-${name}-orders-validation-${RUN_TAG}"
    done
    ;;
  *)
    echo "Usage: bash scripts/run_next_v2.sh {check|baselines|smoke|diagnose|orders}"
    echo "Run each experiment stage once. EVIDENCE_V2_TAG=v2 defaults to new v2 result directories."
    ;;
esac
