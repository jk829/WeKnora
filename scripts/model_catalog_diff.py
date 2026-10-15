#!/usr/bin/env python3
"""比较内置厂商模型目录与 models.dev，输出差异。

仅供开发时使用，不在运行时执行。报告上下文窗口、最大输出、费用及新增/退役 ID，
供维护者手工更新 internal/models/catalog/data/seed.json。兼容性、思考格式等
行为信息不在范围内，需以厂商文档为依据，models.dev 不提供这些信息。

用法：
    scripts/model_catalog_diff.py
    scripts/model_catalog_diff.py --api api.json
    scripts/model_catalog_diff.py --vendor deepseek
    scripts/model_catalog_diff.py --exit-code

默认抓取 https://models.dev/api.json；--api 使用本地副本；
--exit-code 在存在差异时返回非零退出码。结果仅作提示：+ 表示上游新增模型，
~ 表示数值差异，? 表示上游未列出的条目，常见于厂商别名或中国区专用 ID。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "internal/models/catalog/data/models.generated.json"

# WeKnora 厂商 ID 到 models.dev 提供商 ID 的映射。
PROVIDER_MAP = json.loads((ROOT / "scripts/model-catalog/sources.json").read_text())["models_dev"]["provider_map"]


MODELS_DEV_URL = "https://models.dev/api.json"


def load_api(path):
    """从文件加载 models.dev 目录，或执行一次网络抓取。

    models.dev 拒绝默认 urllib 用户代理，因此显式设置代理标识。
    离线或 CI 环境可手动下载，通过 --api 或 MODELS_DEV_API 指定路径。
    """
    path = path or os.environ.get("MODELS_DEV_API")
    if path:
        return json.loads(Path(path).read_text())
    request = urllib.request.Request(
        MODELS_DEV_URL,
        headers={"User-Agent": "WeKnora-model-catalog-diff/1.0 (+https://github.com/Tencent/WeKnora)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.URLError as err:
        raise SystemExit(
            f"failed to fetch {MODELS_DEV_URL}: {err}\n"
            "Download it manually and re-run with --api <file>, or set MODELS_DEV_API."
        ) from err


def load_catalog(vendor):
    entries = json.loads(CATALOG.read_text())["providers"].get(vendor, [])
    return {m["id"]: m for m in entries if m.get("id")}


def compare(vendor, upstream, ours):
    lines = []
    up_models = upstream.get("models", {})
    for mid, spec in sorted(up_models.items()):
        mods = spec.get("modalities", {})
        if "text" not in mods.get("output", ["text"]):
            continue  # 图片及音频生成模型不在比较范围内。
        entry = ours.get(mid)
        limit = spec.get("limit", {})
        cost = spec.get("cost", {})
        if entry is None:
            lines.append(
                f"  + {mid}  (new upstream: ctx={limit.get('context')} out={limit.get('output')} "
                f"reasoning={spec.get('reasoning')} released={spec.get('release_date')})"
            )
            continue
        diffs = []
        if limit.get("context") and entry.get("context_window") != limit.get("context"):
            diffs.append(f"context_window {entry.get('context_window')} -> {limit.get('context')}")
        if limit.get("output") and entry.get("max_output_tokens") != limit.get("output"):
            diffs.append(f"max_output_tokens {entry.get('max_output_tokens')} -> {limit.get('output')}")
        if bool(entry.get("reasoning")) != bool(spec.get("reasoning")):
            diffs.append(f"reasoning {entry.get('reasoning')} -> {spec.get('reasoning')}")
        ours_cost = entry.get("cost") or {}
        for key, up_key in (("input", "input"), ("output", "output"), ("cache_read", "cache_read")):
            if cost.get(up_key) is not None and ours_cost.get(key) != cost.get(up_key):
                diffs.append(f"cost.{key} {ours_cost.get(key)} -> {cost.get(up_key)}")
        if diffs:
            lines.append(f"  ~ {mid}: " + "; ".join(diffs))
    for mid in sorted(ours):
        if mid not in up_models:
            lines.append(f"  ? {mid}  (not in models.dev; keep if the vendor still documents it)")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", help="path to a downloaded models.dev api.json")
    parser.add_argument("--vendor", help="limit to one WeKnora vendor id")
    parser.add_argument(
        "--exit-code", action="store_true",
        help="exit 1 when there are findings (for a scheduled job); default always exits 0",
    )
    args = parser.parse_args()

    api = load_api(args.api)
    vendors = [args.vendor] if args.vendor else sorted(PROVIDER_MAP)
    exit_code = 0
    for vendor in vendors:
        upstream_id = PROVIDER_MAP.get(vendor)
        if not upstream_id:
            print(f"== {vendor}: no models.dev mapping", file=sys.stderr)
            continue
        upstream = api.get(upstream_id)
        if upstream is None:
            print(f"== {vendor}: models.dev provider {upstream_id!r} missing", file=sys.stderr)
            continue
        lines = compare(vendor, upstream, load_catalog(vendor))
        print(f"== {vendor} (models.dev: {upstream_id}) — {len(lines)} finding(s)")
        for line in lines:
            print(line)
        if lines:
            exit_code = 1
    return exit_code if args.exit_code else 0


if __name__ == "__main__":
    sys.exit(main())
