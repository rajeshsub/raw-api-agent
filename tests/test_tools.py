from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.tools.calculator import CalculatorTool
from app.agent.tools.file_ops import FileReadTool, FileWriteTool
from app.agent.tools.web_search import WebSearchTool

# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------


async def test_calculator_basic_arithmetic() -> None:
    tool = CalculatorTool()
    result = await tool.run(expression="2 + 2")
    assert result.success is True
    assert result.output == "4"


async def test_calculator_sqrt() -> None:
    tool = CalculatorTool()
    result = await tool.run(expression="sqrt(144)")
    assert result.success is True
    assert result.output == "12.0"


async def test_calculator_float_ops() -> None:
    tool = CalculatorTool()
    result = await tool.run(expression="150 * 1.1")
    assert result.success is True
    assert float(result.output) == pytest.approx(165.0)


async def test_calculator_missing_expression() -> None:
    tool = CalculatorTool()
    result = await tool.run()
    assert result.success is False
    assert result.error is not None


async def test_calculator_invalid_expression() -> None:
    tool = CalculatorTool()
    result = await tool.run(expression="import os; os.system('evil')")
    assert result.success is False
    assert result.error is not None


async def test_calculator_declaration() -> None:
    tool = CalculatorTool()
    decl = tool.declaration()
    assert decl.name == "calculate"


# ---------------------------------------------------------------------------
# FileReadTool
# ---------------------------------------------------------------------------


async def test_file_read_existing(workspace: Path) -> None:
    (workspace / "hello.txt").write_text("world", encoding="utf-8")
    tool = FileReadTool(workspace=workspace)
    result = await tool.run(path="hello.txt")
    assert result.success is True
    assert result.output == "world"


async def test_file_read_missing(workspace: Path) -> None:
    tool = FileReadTool(workspace=workspace)
    result = await tool.run(path="no_such_file.txt")
    assert result.success is False
    assert "not found" in (result.error or "").lower()


async def test_file_read_traversal_rejected(workspace: Path) -> None:
    tool = FileReadTool(workspace=workspace)
    result = await tool.run(path="../../../etc/passwd")
    assert result.success is False
    assert result.error is not None


async def test_file_read_empty_path(workspace: Path) -> None:
    tool = FileReadTool(workspace=workspace)
    result = await tool.run(path="")
    assert result.success is False


async def test_file_read_declaration(workspace: Path) -> None:
    tool = FileReadTool(workspace=workspace)
    decl = tool.declaration()
    assert decl.name == "file_read"


async def test_file_read_generic_exception(workspace: Path) -> None:
    from unittest.mock import patch

    (workspace / "test.txt").write_text("content", encoding="utf-8")
    tool = FileReadTool(workspace=workspace)
    with patch("pathlib.Path.read_text", side_effect=OSError("disk error")):
        result = await tool.run(path="test.txt")
    assert result.success is False
    assert "disk error" in (result.error or "")


# ---------------------------------------------------------------------------
# FileWriteTool
# ---------------------------------------------------------------------------


async def test_file_write_creates_file(workspace: Path) -> None:
    tool = FileWriteTool(workspace=workspace)
    result = await tool.run(path="output.txt", content="hello world")
    assert result.success is True
    assert (workspace / "output.txt").read_text(encoding="utf-8") == "hello world"


async def test_file_write_creates_parents(workspace: Path) -> None:
    tool = FileWriteTool(workspace=workspace)
    result = await tool.run(path="subdir/nested/file.txt", content="nested")
    assert result.success is True
    assert (workspace / "subdir" / "nested" / "file.txt").exists()


async def test_file_write_traversal_rejected(workspace: Path) -> None:
    tool = FileWriteTool(workspace=workspace)
    result = await tool.run(path="../evil.txt", content="bad")
    assert result.success is False
    assert result.error is not None


async def test_file_write_empty_path(workspace: Path) -> None:
    tool = FileWriteTool(workspace=workspace)
    result = await tool.run(path="", content="data")
    assert result.success is False


async def test_file_write_reports_bytes(workspace: Path) -> None:
    tool = FileWriteTool(workspace=workspace)
    result = await tool.run(path="report.txt", content="abc")
    assert result.success is True
    assert "3" in result.output


async def test_file_write_declaration(workspace: Path) -> None:
    tool = FileWriteTool(workspace=workspace)
    decl = tool.declaration()
    assert decl.name == "file_write"


# ---------------------------------------------------------------------------
# WebSearchTool
# ---------------------------------------------------------------------------


async def test_web_search_success() -> None:
    gemini = MagicMock()
    gemini.search = AsyncMock(return_value="Top news: India wins cricket match.")
    tool = WebSearchTool(gemini=gemini)
    result = await tool.run(query="latest India news")
    assert result.success is True
    assert "India" in result.output
    gemini.search.assert_awaited_once_with("latest India news")


async def test_web_search_empty_query() -> None:
    tool = WebSearchTool(gemini=MagicMock())
    result = await tool.run(query="")
    assert result.success is False
    assert result.error == "query is required"


async def test_web_search_missing_query() -> None:
    tool = WebSearchTool(gemini=MagicMock())
    result = await tool.run()
    assert result.success is False
    assert result.error == "query is required"


async def test_web_search_gemini_error() -> None:
    gemini = MagicMock()
    gemini.search = AsyncMock(side_effect=RuntimeError("API down"))
    tool = WebSearchTool(gemini=gemini)
    result = await tool.run(query="news")
    assert result.success is False
    assert "API down" in (result.error or "")


async def test_web_search_declaration() -> None:
    tool = WebSearchTool(gemini=MagicMock())
    decl = tool.declaration()
    assert decl.name == "web_search"


async def test_file_write_generic_exception(workspace: Path) -> None:
    from unittest.mock import patch

    tool = FileWriteTool(workspace=workspace)
    with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
        result = await tool.run(path="output.txt", content="data")
    assert result.success is False
    assert "disk full" in (result.error or "")
