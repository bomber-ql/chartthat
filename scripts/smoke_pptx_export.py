"""十三图型 /api/generate-pptx 导出冒烟（SPEC §6 M4，v1.6）。

用法：python3 scripts/smoke_pptx_export.py [base_url]
逐型 POST 自描述单图请求，断言：HTTP 200、PK 魔数、Content-Disposition 文件名
为 .pptx、chart XML 含预期 plot 标记、rels 无 TargetMode="External"（C-2）。
pipeline 会给 curl 追加 -w 尾巴污染落盘文件，故用 urllib 串联。
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.request
import zipfile

BASE = sys.argv[1] if len(sys.argv) > 1 else f"http://localhost:{os.environ.get('DEPLOY_RUN_PORT', '5000')}"


def s(name: str, data: list, unit: str = "yi", **kw) -> dict:
    return {"name": name, "unit": unit, "data": data, **kw}


# chart_type -> (请求 data, chart XML 预期标记)
CASES: dict[str, tuple[dict, str]] = {
    "line": ({"categories": ["a", "b", "c"], "series": [s("趋势", [1.0, None, 3.0])]}, "<c:lineChart>"),
    "bar": ({"categories": ["a", "b"], "series": [s("体量", [1.0, 2.0])]}, "<c:barChart>"),
    "hbar": ({"categories": ["a", "b"], "series": [s("体量", [1.0, 2.0])]}, '<c:barDir val="bar"/>'),
    "area": ({"categories": ["a", "b"], "series": [s("营收", [1.0, 2.0])]}, "<c:areaChart>"),
    "combo": ({"categories": ["a", "b"],
               "series": [s("体量", [1.0, 2.0], kind="bar"),
                          s("同比", [0.1, 0.2], unit="percent", kind="line", axis="secondary")]},
              "<c:lineChart>"),
    "stacked": ({"categories": ["a", "b"], "series": [s("移动", [1.0, 2.0]), s("PC", [3.0, 4.0])]},
                '<c:grouping val="stacked"/>'),
    "slope": ({"categories": ["a", "b"], "series": [s("2024", [1.0, 2.0]), s("2025", [2.0, 3.0])]},
              "<c:lineChart>"),
    "scatter": ({"categories": ["a", "b"], "series": [s("X", [1.0, 2.0]), s("Y", [3.0, 4.0])]},
                "<c:scatterChart>"),
    "waterfall": ({"categories": ["a", "b", "c"], "series": [s("变化", [10.0, -3.0, 1.0])]},
                  "<a:noFill/>"),
    "radar": ({"categories": ["m1", "m2", "m3"],
               "series": [s("A", [1.0, 2.0, 3.0], unit="count"),
                          s("B", [2.0, 3.0, 1.0], unit="count"),
                          s("C", [3.0, 1.0, 2.0], unit="count")]},
              "<c:radarChart>"),
    "pie": ({"categories": ["a", "b"], "series": [s("份额", [1.0, 2.0])]}, "<c:pieChart>"),
    "donut": ({"categories": ["a", "b"], "series": [s("份额", [1.0, 2.0])]}, "<c:doughnutChart>"),
    "sunburst": ({"categories": ["a", "b"], "series": [s("份额", [1.0, 2.0])]}, "<c:doughnutChart>"),
}


def main() -> int:
    ok = 0
    for chart_type, (data, marker) in CASES.items():
        body = json.dumps({"chart_type": chart_type, "data": data}).encode()
        req = urllib.request.Request(
            f"{BASE}/api/generate-pptx", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            blob = resp.read()
            disposition = resp.headers.get("Content-Disposition", "")
        assert blob[:2] == b"PK", f"{chart_type}: 响应非 pptx（PK 魔数缺失）"
        assert ".pptx" in disposition, f"{chart_type}: 文件名非 .pptx（{disposition}）"
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            names = zf.namelist()
            chart_names = [n for n in names if n.startswith("ppt/charts/chart") and n.endswith(".xml")]
            assert chart_names, f"{chart_type}: 包内无 chart XML"
            xml = zf.read(chart_names[0]).decode("utf-8")
            rels = "".join(
                zf.read(n).decode("utf-8") for n in names if n.startswith("ppt/charts/_rels/")
            )
        assert marker in xml, f"{chart_type}: chart XML 缺少标记 {marker}"
        assert 'TargetMode="External"' not in rels, f"{chart_type}: 存在外部数据链接（C-2 违反）"
        print(f"  PASS {chart_type:<10} {len(blob):>6} bytes  marker={marker}")
        ok += 1
    print(f"十三图型导出冒烟全部通过（{ok}/{len(CASES)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
