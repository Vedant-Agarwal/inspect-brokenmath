# MANAGED FILE - Updates pulled from template. See MANAGED_FILES.md
"""Unit tests for add_readme_section.py script."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from add_readme_section import (  # noqa: E402
    add_section_tags,
    find_insertion_point,
    has_section_tags,
    normalize_key,
)


class TestNormalizeKey:
    def test_without_suffix(self) -> None:
        assert normalize_key("Parameters") == "Parameters: Automatically Generated"

    def test_with_suffix(self) -> None:
        assert (
            normalize_key("Parameters: Automatically Generated")
            == "Parameters: Automatically Generated"
        )

    def test_various_keys(self) -> None:
        assert normalize_key("Options") == "Options: Automatically Generated"
        assert normalize_key("Usage") == "Usage: Automatically Generated"
        assert normalize_key("Contributors") == "Contributors: Automatically Generated"


class TestHasSectionTags:
    def test_when_present(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Test\n\n"
            "<!-- Parameters: Automatically Generated -->\n"
            "Some content\n"
            "<!-- /Parameters: Automatically Generated -->\n"
        )
        assert has_section_tags(readme, "Parameters") is True

    def test_when_absent(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("# Test\n\nSome content\n")
        assert has_section_tags(readme, "Parameters") is False

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        readme = tmp_path / "nonexistent.md"
        assert has_section_tags(readme, "Parameters") is False

    def test_normalizes_key(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Test\n\n"
            "<!-- Parameters: Automatically Generated -->\n"
            "<!-- /Parameters: Automatically Generated -->\n"
        )
        assert has_section_tags(readme, "Parameters") is True
        assert has_section_tags(readme, "Parameters: Automatically Generated") is True


class TestFindInsertionPoint:
    def test_after_html_tag(self) -> None:
        lines = [
            "# README",
            "",
            "<!-- Options: Automatically Generated -->",
            "Options content",
            "<!-- /Options: Automatically Generated -->",
            "",
            "## More content",
        ]
        assert find_insertion_point(lines, ["Options"]) == 5

    def test_priority_order(self) -> None:
        lines = [
            "# README",
            "<!-- Usage: Automatically Generated -->",
            "<!-- /Usage: Automatically Generated -->",
            "",
            "<!-- Options: Automatically Generated -->",
            "<!-- /Options: Automatically Generated -->",
        ]
        assert find_insertion_point(lines, ["Options", "Usage"]) == 6

    def test_fallback_to_second_priority(self) -> None:
        lines = [
            "# README",
            "<!-- Usage: Automatically Generated -->",
            "<!-- /Usage: Automatically Generated -->",
            "",
            "## More content",
        ]
        assert find_insertion_point(lines, ["Options", "Usage"]) == 3

    def test_none_found(self) -> None:
        lines = ["# README", "", "Some content"]
        assert find_insertion_point(lines, ["Options", "Usage"]) is None

    def test_manual_markdown_header(self) -> None:
        lines = [
            "# README",
            "",
            "## Usage",
            "",
            "Some usage instructions",
            "",
            "## More Sections",
        ]
        assert find_insertion_point(lines, ["Usage"]) == 6

    def test_skips_code_blocks(self) -> None:
        lines = [
            "# README",
            "",
            "## Usage",
            "",
            "```bash",
            "# Evaluate full dataset",
            "inspect eval my_eval/task",
            "```",
            "",
            "## Dataset",
        ]
        assert find_insertion_point(lines, ["Usage"]) == 9


class TestAddSectionTags:
    def test_after_options(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Test\n\n"
            "<!-- Options: Automatically Generated -->\n"
            "Options content\n"
            "<!-- /Options: Automatically Generated -->\n\n"
            "## More content\n"
        )

        result = add_section_tags(readme, "Parameters", ["Options"])
        assert result is True

        content = readme.read_text()
        assert "<!-- Parameters: Automatically Generated -->" in content
        assert "<!-- /Parameters: Automatically Generated -->" in content

    def test_append_to_end(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("# Test\n\nSome content\n")

        result = add_section_tags(readme, "Parameters", ["Options"])
        assert result is True

        content = readme.read_text()
        assert "<!-- Parameters: Automatically Generated -->" in content

    def test_already_exists(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        original = (
            "# Test\n\n"
            "<!-- Parameters: Automatically Generated -->\n"
            "Existing\n"
            "<!-- /Parameters: Automatically Generated -->\n"
        )
        readme.write_text(original)

        result = add_section_tags(readme, "Parameters", ["Options"])
        assert result is False
        assert readme.read_text() == original

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        readme = tmp_path / "nonexistent.md"
        assert add_section_tags(readme, "Parameters", ["Options"]) is False
