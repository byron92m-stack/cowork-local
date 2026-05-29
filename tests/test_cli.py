from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.powerpoint_creator.cli import build_parser, main, parse_chart_arg, parse_table_arg


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

class TestBuildParser:
    def test_default_output(self):
        parser = build_parser()
        ns = parser.parse_args([])
        assert ns.output == "output.pptx"

    def test_custom_output(self):
        parser = build_parser()
        ns = parser.parse_args(["-o", "my.pptx"])
        assert ns.output == "my.pptx"

    def test_title_flag(self):
        parser = build_parser()
        ns = parser.parse_args(["-t", "My Title"])
        assert ns.title == "My Title"

    def test_subtitle_flag(self):
        parser = build_parser()
        ns = parser.parse_args(["-st", "Sub"])
        assert ns.subtitle == "Sub"

    def test_slides_flag(self):
        parser = build_parser()
        ns = parser.parse_args(["-s", "5"])
        assert ns.slides == 5

    def test_font_size_flag(self):
        parser = build_parser()
        ns = parser.parse_args(["--font-size", "24"])
        assert ns.font_size == 24

    def test_image_flag(self):
        parser = build_parser()
        ns = parser.parse_args(["-i", "img1.png", "img2.png"])
        assert ns.image == ["img1.png", "img2.png"]

    def test_quiet_flag(self):
        parser = build_parser()
        ns = parser.parse_args(["-q"])
        assert ns.quiet is True


# ---------------------------------------------------------------------------
# parse_table_arg
# ---------------------------------------------------------------------------

class TestParseTableArg:
    def test_parses_correctly(self):
        headers, rows = parse_table_arg("Name,Age|Alice,30;Bob,25")
        assert headers == ["Name", "Age"]
        assert rows == [["Alice", "30"], ["Bob", "25"]]

    def test_missing_pipe_raises(self):
        with pytest.raises(ValueError, match="Table must be formatted"):
            parse_table_arg("Name,Age")

    def test_handles_empty_cells(self):
        headers, rows = parse_table_arg("A,B|,1;2,")
        assert headers == ["A", "B"]
        assert rows == [["", "1"], ["2", ""]]


# ---------------------------------------------------------------------------
# parse_chart_arg
# ---------------------------------------------------------------------------

class TestParseChartArg:
    def test_parses_correctly(self):
        ct, cats, series = parse_chart_arg("bar:Q1,Q2:Sales=100,200")
        assert ct == "bar"
        assert cats == ["Q1", "Q2"]
        assert series == {"Sales": [100.0, 200.0]}

    def test_missing_segments_raises(self):
        with pytest.raises(ValueError, match="Chart must be formatted"):
            parse_chart_arg("bar:cats")

    def test_multi_series(self):
        ct, cats, series = parse_chart_arg("line:A,B:X=1,2;Y=3,4")
        assert ct == "line"
        assert cats == ["A", "B"]
        assert series == {"X": [1.0, 2.0], "Y": [3.0, 4.0]}


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

class TestMain:
    def test_creates_pptx(self, tmp_path):
        out = tmp_path / "t.pptx"
        rc = main(["-o", str(out), "-t", "Test", "-q"])
        assert rc == 0
        assert out.exists()

    def test_nonexistent_image_returns_error(self, tmp_path):
        out = tmp_path / "t.pptx"
        rc = main(["-o", str(out), "-i", "no-such.png", "-q"])
        assert rc == 1

    def test_bad_chart_type_returns_error(self, tmp_path):
        out = tmp_path / "t.pptx"
        rc = main(["-o", str(out), "--chart", "invalid:A:V=1", "-q"])
        assert rc == 1

    def test_bad_table_format_returns_error(self, tmp_path):
        out = tmp_path / "t.pptx"
        rc = main(["-o", str(out), "--table", "badformat", "-q"])
        assert rc == 1

    def test_success_message_when_not_quiet(self, tmp_path, capsys):
        out = tmp_path / "t.pptx"
        rc = main(["-o", str(out), "-t", "Hi"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "Presentation saved to" in captured.out

    def test_template_not_found_returns_error(self, tmp_path):
        out = tmp_path / "t.pptx"
        rc = main(["-o", str(out), "--template", "missing.pptx", "-q"])
        assert rc == 1
