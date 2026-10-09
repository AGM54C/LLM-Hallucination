#!/usr/bin/env bash
# Development controls. Uses the migrated CUDA environment and never retrains.
set -euo pipefail
cd /data/coding/scientific-evidence-learning

PYTHON_BIN=${EVIDENCE_PYTHON:-/data/miniconda/envs/torch/bin/python}
MODEL_DIR=/data/coding/models/Qwen3-14B
DATASET=artifacts/server-dataset-with-difficulty-v1
ADAPTER=checkpoints/qwen3-14b-uniform-s41/adapter
RUN_TAG=${EVIDENCE_V3_TAG:-v3}
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
if [[ ! "$RUN_TAG" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo "EVIDENCE_V3_TAG must use letters, digits, underscores or hyphens." >&2
  exit 2
fi
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python not found: $PYTHON_BIN. Set EVIDENCE_PYTHON to the CUDA environment interpreter." >&2
  exit 2
fi

run_logged() {
  local label=$1
  shift
  mkdir -p logs
  local logfile="logs/${label}.log"
  (set -o noclobber; : > "$logfile") || {
    echo "Log already exists. Keep it and use a new EVIDENCE_V3_TAG for a rerun." >&2
    return 2
  }
  "$@" 2>&1 | tee "$logfile"
}

control_model() {
  local name=$1
  local stage=$2
  shift 2
  local extra=()
  if [[ "$name" == uniform ]]; then extra=(--adapter "$ADAPTER"); fi
  run_logged "qwen3-14b-${name}-controls-${stage}-${RUN_TAG}" \
    "$PYTHON_BIN" run_v3.py --dataset "$DATASET" --model "$MODEL_DIR" \
    "${extra[@]}" --readouts "artifacts/qwen3-14b-${name}-readouts-validation-v2" \
    --device cuda --thinking-mode off --objectives conditional_max conditional_min \
    --out "artifacts/qwen3-14b-${name}-controls-${stage}-${RUN_TAG}" "$@"
}

case "${1:-help}" in
  check)
    "$PYTHON_BIN" -c 'import sys,torch,transformers,peft; print(sys.executable); print("torch",torch.__version__,"transformers",transformers.__version__,"peft",peft.__version__); assert torch.cuda.is_available()'
    "$PYTHON_BIN" run.py verify --dataset "$DATASET"
    "$PYTHON_BIN" -m unittest discover -s tests -p 'test_v[23].py' -v
    bash -n scripts/run_next_v3.sh
    for name in base uniform; do
      extra=()
      if [[ "$name" == uniform ]]; then extra=(--adapter "$ADAPTER"); fi
      "$PYTHON_BIN" run_v3.py --dataset "$DATASET" --model "$MODEL_DIR" "${extra[@]}" \
        --readouts "artifacts/qwen3-14b-${name}-readouts-validation-v2" \
        --out "artifacts/preview-controls-${name}-never-written" --dry-run
    done
    ;;
  audit)
    run_logged "training-pool-audit-${RUN_TAG}" "$PYTHON_BIN" scripts/audit_training_pool_v3.py \
      --dataset "$DATASET" --model "$MODEL_DIR" --out "artifacts/training-pool-audit-${RUN_TAG}.json"
    ;;
  smoke|controls)
    mkdir -p logs
    exec 9>logs/v3-gpu.lock
    flock -n 9 || { echo "Another V3 GPU stage holds the lock." >&2; exit 2; }
    if [[ "$1" == smoke ]]; then
      for name in base uniform; do control_model "$name" smoke --limit 24; done
    else
      # Format-only gate. Scientific accuracy is not a criterion for allowing a full run.
      "$PYTHON_BIN" - "$RUN_TAG" <<'PY'
import json
import sys
from pathlib import Path
tag = sys.argv[1]
for name in ['base', 'uniform']:
    path = Path(f'artifacts/qwen3-14b-{name}-controls-smoke-{tag}')
    summary = json.loads((path / 'summary.json').read_text())
    assert summary['status'] == 'complete' and summary['requests'] == 120, path
    assert not (path / 'failure.json').exists(), path
    invalid = {key: value['invalid'] for key, value in summary['endpoints'].items() if value['invalid']}
    if invalid:
        raise SystemExit(f'Inspect smoke format failures before a full run: {name} {invalid}')
print('SMOKE_FORMAT_GATE_OK')
PY
      for name in base uniform; do control_model "$name" validation; done
    fi
    ;;
  *)
    echo "Usage: bash scripts/run_next_v3.sh {check|audit|smoke|controls}"
    echo "check/audit use CPU; smoke=240 new model calls total; controls=3300 total."
    ;;
esac
