"""业务模块包（SPEC §6 M1-M4）。

对外门面：
- parse_input(raw_text)：M1+M2 串联，原始文本 → SemanticTable（SPEC §5.3）。
"""
from __future__ import annotations

from typing import Any

from app.modules.parser import ParseError, parse_bytes, parse_text
from app.modules.semantic import analyze_table

__all__ = ["ParseError", "analyze_table", "parse_bytes", "parse_input", "parse_text"]


def parse_input(raw_text: str) -> dict[str, Any]:
    """模块对外入口：原始文本 → SemanticTable（M1 切分 + M2 语义分析）。"""
    return analyze_table(parse_text(raw_text))
