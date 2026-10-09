"""离线重建公开 V4/V5 的提示、评分与汇总；不加载模型、不联网。"""
# ruff: noqa: E402 -- 直接运行时先定位仓库内的冻结包。
from __future__ import annotations

import hashlib
import json
import math
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "scientific-evidence-learning"
sys.path.insert(0, str(PROJECT / "src"))

from evidence_lab.data import case_from_dict
from evidence_lab.models import Completion
from evidence_lab_v4.factorial import joint_prompt, remap_presentation, score_response
from evidence_lab_v4.reporting import summarize as summarize_v4
from evidence_lab_v5.controls import conditions_for, make_record
from evidence_lab_v5.reporting import summarize as summarize_v5


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_archive(path):
    with zipfile.ZipFile(path) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), "重复归档条目")
        manifest = json.loads(archive.read("SHA256.json"))
        require(set(archive.namelist()) == set(manifest) | {"SHA256.json"}, "归档清单不完整")
        files = {}
        for name, info in manifest.items():
            raw = archive.read(name)
            require(len(raw) == info["bytes"], name + " 字节数变化")
            require(hashlib.sha256(raw).hexdigest() == info["sha256"], name + " 哈希变化")
            files[name] = raw
        return files


def rows(raw):
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]


def check_summary(actual, expected):
    for key, value in actual.items():
        require(expected.get(key) == value, "汇总不一致：" + key)


def main():
    dataset = read_archive(ROOT / "results/dataset/冻结数据.zip")
    freeze = json.loads(dataset["freeze.json"])
    for name, expected in freeze["files"].items():
        require(name in dataset, "缺少冻结文件：" + name)
        require(hashlib.sha256(dataset[name]).hexdigest() == expected, "数据冻结哈希变化：" + name)
    cases = {case.case_id: case for case in map(case_from_dict, rows(dataset["cases.jsonl"]))}
    v4 = read_archive(ROOT / "results/v4/原始记录.zip")
    v5 = read_archive(ROOT / "results/v5/原始记录.zip")
    for model in ["base", "uniform"]:
        old = f"qwen3-14b-{model}-factorial-validation-v4/"
        new = f"qwen3-14b-{model}-context-validation-v5/"
        spec = json.loads(v5[new + "specification.json"])
        require(hashlib.sha256(dataset["freeze.json"]).hexdigest() == spec["dataset_freeze_sha256"], "数据版本不一致")
        for name, expected in spec["code_files_sha256"].items():
            require(hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() == expected, "冻结源码变化：" + name)
        for name, expected in spec["source_files_sha256"].items():
            require(hashlib.sha256(v4[old + name]).hexdigest() == expected, "V4 缓存来源变化：" + name)
        source_rows = rows(v4[old + "responses.jsonl"])
        require(len(source_rows) == 2640 and len({r["request_id"] for r in source_rows}) == 2640, "V4 缺失或重复")
        for row in source_rows:
            case = cases[row["case_id"]]
            condition = {key: row[key] for key in ["variant", "alias_rotation", "output_order"]}
            presentation = remap_presentation(case, row["variant"], row["alias_rotation"])
            prompt = joint_prompt(case, presentation, row["output_order"])
            require(row["prompt"] == prompt, "V4 提示变化")
            require(row["prompt_sha256"] == hashlib.sha256(prompt.encode()).hexdigest(), "V4 提示哈希变化")
            evaluation = score_response(case, condition, presentation, row["response"])
            require(row["evaluation"] == evaluation, "V4 评分变化")
        check_summary(summarize_v4(source_rows, json.loads(v4[old + "protocol.json"])), json.loads(v4[old + "summary.json"]))
        protocol = json.loads(v5[new + "protocol.json"])
        current_rows = rows(v5[new + "responses.jsonl"])
        expected_requests = [(source, context) for source in source_rows for context in conditions_for(source, protocol)]
        require(len(current_rows) == len(expected_requests) == 5280, "V5 请求数变化")
        require(len({r["request_id"] for r in current_rows}) == 5280, "V5 重复请求")
        for row, (source, context) in zip(current_rows, expected_requests):
            require(math.isfinite(row["elapsed_seconds"]) and row["elapsed_seconds"] >= 0, "无效耗时")
            completion = Completion(row["response"], row["input_tokens"], row["output_tokens"]) if row["executed"] else None
            expected = make_record(cases[source["case_id"]], source, context, completion, row["elapsed_seconds"], protocol)
            require(row == expected, "V5 提示、数值字面量、顺序或评分变化")
        summary = summarize_v5(current_rows, protocol)
        check_summary(summary, json.loads(v5[new + "summary.json"]))
        # 直接计数再核对主要分母，避免仅依赖汇总函数。
        for context in ["numbers_only", "table_and_numbers"]:
            subset = [r for r in current_rows if r["context"] == context]
            counts = Counter(r["scores"]["decision"]["correct"] is True for r in subset)
            require(len(subset) == 2640, "条件分母变化")
            require(sum(r["executed"] for r in subset) == 2636, "执行分母变化")
            acc = counts[True] / len(subset)
            require(acc == summary["by_context"][context]["decision"]["all_attempt_accuracy"], "准确率分母不一致")
            print(f"{model:7s} {context:17s} {counts[True]}/2640 = {acc:.4%}")
        print(f"{model}: V4 2640 条、V5 5280 条全部重建一致")
    print("通过：归档哈希、冻结源码、数据、V4 缓存、V4/V5 提示与评分、汇总。未加载模型。")


if __name__ == "__main__":
    main()
