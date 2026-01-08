"""Index consistency tests - verify index files match actual files on disk.

These tests run on every PR (no external dependencies required).
They ensure our documentation indexes stay synchronized with reality.

Index files verified:
- docs/0200-ADR-index.md (ADR registry)
- docs/0800-audit-index.md (Audit registry)
- docs/0100-TEMPLATE-GUIDE.md (Template registry)
- docs/0600-skill-instructions-index.md (Skill instructions registry)
"""

import re
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = REPO_ROOT / "docs"


def extract_links_from_markdown(content: str, pattern: str) -> set[str]:
    """Extract markdown links matching a pattern from content.

    Args:
        content: Markdown file content
        pattern: Regex pattern to match (e.g., r'02\\d{2}-ADR-.*\\.md')

    Returns:
        Set of linked filenames
    """
    # Match markdown links: [text](filename.md) or [text](./filename.md)
    link_pattern = rf"\[.*?\]\(\.?/?({pattern})\)"
    matches = re.findall(link_pattern, content)
    return set(matches)


class TestIndexConsistency:
    """Verify index files match actual files on disk."""

    def test_adr_index_complete(self) -> None:
        """Verify all ADR files are listed in 0200-ADR-index.md.

        ADRs document architectural decisions. Missing entries mean
        undocumented decisions that future developers can't find.
        """
        index_file = DOCS_DIR / "0200-ADR-index.md"
        assert index_file.exists(), "ADR index not found"

        # Find actual ADR files (excluding the index itself)
        actual_adrs = {
            f.name
            for f in DOCS_DIR.glob("02*-ADR-*.md")
            if f.name != "0200-ADR-index.md"
        }

        # Extract ADRs referenced in index
        content = index_file.read_text(encoding="utf-8")
        indexed_adrs = extract_links_from_markdown(content, r"02\d{2}-ADR-[^)]+\.md")

        # Check for missing entries
        missing = actual_adrs - indexed_adrs
        assert not missing, (
            "ADR INDEX DRIFT: Files exist but not in index:\n"
            + "\n".join(f"  - {f}" for f in sorted(missing))
            + "\n\nAdd these to docs/0200-ADR-index.md"
        )

        # Check for orphaned entries (index references non-existent files)
        orphaned = indexed_adrs - actual_adrs
        assert not orphaned, (
            "ADR INDEX DRIFT: Index references non-existent files:\n"
            + "\n".join(f"  - {f}" for f in sorted(orphaned))
            + "\n\nRemove these from docs/0200-ADR-index.md"
        )

    def test_audit_index_complete(self) -> None:
        """Verify all audit files are listed in 0800-audit-index.md.

        Missing audit entries mean audits that won't be scheduled or run.
        """
        index_file = DOCS_DIR / "0800-audit-index.md"
        assert index_file.exists(), "Audit index not found"

        # Find actual audit files (excluding the index itself)
        actual_audits = {
            f.name
            for f in DOCS_DIR.glob("08*-audit-*.md")
            if f.name != "0800-audit-index.md"
        }

        # Extract audits referenced in index (section 9.1 has the links)
        content = index_file.read_text(encoding="utf-8")
        indexed_audits = extract_links_from_markdown(
            content, r"08\d{2}-audit-[^)]+\.md"
        )

        # Check for missing entries
        missing = actual_audits - indexed_audits
        assert not missing, (
            "AUDIT INDEX DRIFT: Files exist but not in index:\n"
            + "\n".join(f"  - {f}" for f in sorted(missing))
            + "\n\nAdd these to docs/0800-audit-index.md section 9.1"
        )

        # Check for orphaned entries
        orphaned = indexed_audits - actual_audits
        assert not orphaned, (
            "AUDIT INDEX DRIFT: Index references non-existent files:\n"
            + "\n".join(f"  - {f}" for f in sorted(orphaned))
            + "\n\nRemove these from docs/0800-audit-index.md"
        )

    def test_template_index_complete(self) -> None:
        """Verify all template files are listed in 0100-TEMPLATE-GUIDE.md.

        Templates ensure consistent documentation. Missing entries mean
        templates that developers won't discover.
        """
        index_file = DOCS_DIR / "0100-TEMPLATE-GUIDE.md"
        assert index_file.exists(), "Template guide not found"

        # Find actual template files (pattern: 01xx-TEMPLATE-*.md)
        actual_templates = {
            f.name
            for f in DOCS_DIR.glob("01*-TEMPLATE-*.md")
            if f.name != "0100-TEMPLATE-GUIDE.md"
        }

        # Extract templates referenced in index
        content = index_file.read_text(encoding="utf-8")

        # Templates are listed as `filename.md` in table cells
        # Match patterns like: | `0101-TEMPLATE-issue.md` |
        # Only match templates marked as "Active" (exclude "Future" planned templates)
        template_pattern = r"\| `(01\d{2}-TEMPLATE-[^`]+\.md)` \|[^|]+\| Active \|"
        indexed_templates = set(re.findall(template_pattern, content))

        # Check for missing entries (actual files not in "Active" index entries)
        missing = actual_templates - indexed_templates
        assert not missing, (
            "TEMPLATE INDEX DRIFT: Files exist but not in index:\n"
            + "\n".join(f"  - {f}" for f in sorted(missing))
            + "\n\nAdd these to docs/0100-TEMPLATE-GUIDE.md"
        )

        # Note: We don't check for orphaned entries because the index
        # legitimately contains "Future" placeholders for planned templates

    def test_skill_instructions_index_complete(self) -> None:
        """Verify all skill instruction files are listed in 0600 index.

        Skill instructions are prompts/procedures for specific tasks.
        Missing entries mean skills that agents won't discover.
        """
        index_file = DOCS_DIR / "0600-skill-instructions-index.md"

        # Skip if index doesn't exist yet (will be created)
        if not index_file.exists():
            return  # Index not yet created

        # Find actual skill instruction files
        actual_skills = {
            f.name
            for f in DOCS_DIR.glob("06*-skill-*.md")
            if f.name != "0600-skill-instructions-index.md"
        }

        # Extract skills referenced in index (exclude the index file itself)
        content = index_file.read_text(encoding="utf-8")
        indexed_skills = extract_links_from_markdown(
            content, r"06\d{2}-skill-[^)]+\.md"
        )
        indexed_skills.discard("0600-skill-instructions-index.md")

        # Check for missing entries
        missing = actual_skills - indexed_skills
        assert not missing, (
            "SKILL INDEX DRIFT: Files exist but not in index:\n"
            + "\n".join(f"  - {f}" for f in sorted(missing))
            + "\n\nAdd these to docs/0600-skill-instructions-index.md"
        )

        # Check for orphaned entries
        orphaned = indexed_skills - actual_skills
        assert not orphaned, (
            "SKILL INDEX DRIFT: Index references non-existent files:\n"
            + "\n".join(f"  - {f}" for f in sorted(orphaned))
            + "\n\nRemove these from docs/0600-skill-instructions-index.md"
        )


class TestIndexCrossReferences:
    """Verify indexes don't have broken cross-references."""

    def test_adr_index_next_number_current(self) -> None:
        """Verify ADR index 'next available number' is accurate."""
        index_file = DOCS_DIR / "0200-ADR-index.md"
        content = index_file.read_text(encoding="utf-8")

        # Extract "next available number" from content
        match = re.search(r"next available number \(currently (\d+)\)", content)
        assert match, "ADR index missing 'next available number' statement"

        claimed_next = int(match.group(1))

        # Find highest actual ADR number
        adr_numbers = []
        for f in DOCS_DIR.glob("02*-ADR-*.md"):
            num_match = re.match(r"(\d+)-ADR-", f.name)
            if num_match:
                adr_numbers.append(int(num_match.group(1)))

        if adr_numbers:
            highest = max(adr_numbers)
            expected_next = highest + 1

            assert claimed_next == expected_next, (
                f"ADR index 'next available number' is stale: "
                f"claims {claimed_next}, should be {expected_next}"
            )
