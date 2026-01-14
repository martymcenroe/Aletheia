"""Index consistency tests - verify index files match actual files on disk.

These tests run on every PR (no external dependencies required).
They ensure our documentation indexes stay synchronized with reality.

Index files verified (10xxx scheme):
- docs/adrs/10200-ADR-index.md (ADR registry)
- docs/audits/10800-audit-index.md (Audit registry)
- docs/templates/10100-TEMPLATE-GUIDE.md (Template registry)
- docs/skills/10600-skill-instructions-index.md (Skill instructions registry)
"""

import re
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = REPO_ROOT / "docs"

# Subdirectories for 10xxx scheme
ADRS_DIR = DOCS_DIR / "adrs"
AUDITS_DIR = DOCS_DIR / "audits"
TEMPLATES_DIR = DOCS_DIR / "templates"
SKILLS_DIR = DOCS_DIR / "skills"


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
        """Verify all ADR files are listed in 10200-ADR-index.md.

        ADRs document architectural decisions. Missing entries mean
        undocumented decisions that future developers can't find.
        """
        index_file = ADRS_DIR / "10200-ADR-index.md"
        assert index_file.exists(), "ADR index not found at docs/adrs/10200-ADR-index.md"

        # Find actual ADR files (excluding the index itself)
        actual_adrs = {
            f.name
            for f in ADRS_DIR.glob("102*-ADR-*.md")
            if f.name != "10200-ADR-index.md"
        }

        # Extract ADRs referenced in index
        content = index_file.read_text(encoding="utf-8")
        indexed_adrs = extract_links_from_markdown(content, r"102\d{2}-ADR-[^)]+\.md")

        # Check for missing entries
        missing = actual_adrs - indexed_adrs
        assert not missing, (
            "ADR INDEX DRIFT: Files exist but not in index:\n"
            + "\n".join(f"  - {f}" for f in sorted(missing))
            + "\n\nAdd these to docs/adrs/10200-ADR-index.md"
        )

        # Check for orphaned entries (index references non-existent files)
        orphaned = indexed_adrs - actual_adrs
        assert not orphaned, (
            "ADR INDEX DRIFT: Index references non-existent files:\n"
            + "\n".join(f"  - {f}" for f in sorted(orphaned))
            + "\n\nRemove these from docs/adrs/10200-ADR-index.md"
        )

    def test_audit_index_complete(self) -> None:
        """Verify all audit files are listed in 10800-audit-index.md.

        Missing audit entries mean audits that won't be scheduled or run.
        """
        index_file = AUDITS_DIR / "10800-audit-index.md"
        assert index_file.exists(), "Audit index not found at docs/audits/10800-audit-index.md"

        # Find actual audit files (excluding the index itself)
        actual_audits = {
            f.name
            for f in AUDITS_DIR.glob("108*-audit-*.md")
            if f.name != "10800-audit-index.md"
        }

        # Extract audits referenced in index (section 10.1 has the links)
        content = index_file.read_text(encoding="utf-8")
        indexed_audits = extract_links_from_markdown(
            content, r"108\d{2}-audit-[^)]+\.md"
        )

        # Check for missing entries
        missing = actual_audits - indexed_audits
        assert not missing, (
            "AUDIT INDEX DRIFT: Files exist but not in index:\n"
            + "\n".join(f"  - {f}" for f in sorted(missing))
            + "\n\nAdd these to docs/audits/10800-audit-index.md section 10.1"
        )

        # Check for orphaned entries
        orphaned = indexed_audits - actual_audits
        assert not orphaned, (
            "AUDIT INDEX DRIFT: Index references non-existent files:\n"
            + "\n".join(f"  - {f}" for f in sorted(orphaned))
            + "\n\nRemove these from docs/audits/10800-audit-index.md"
        )

    def test_template_index_complete(self) -> None:
        """Verify all template files are listed in 10100-TEMPLATE-GUIDE.md.

        Templates ensure consistent documentation. Missing entries mean
        templates that developers won't discover.
        """
        index_file = TEMPLATES_DIR / "10100-TEMPLATE-GUIDE.md"
        assert index_file.exists(), "Template guide not found at docs/templates/10100-TEMPLATE-GUIDE.md"

        # Find actual template files (pattern: 101xx-TEMPLATE-*.md)
        actual_templates = {
            f.name
            for f in TEMPLATES_DIR.glob("101*-TEMPLATE-*.md")
            if f.name != "10100-TEMPLATE-GUIDE.md"
        }

        # Extract templates referenced in index
        content = index_file.read_text(encoding="utf-8")

        # Templates are listed as `filename.md` in table cells
        # Match patterns like: | `10101-TEMPLATE-issue.md` |
        # Only match templates marked as "Active" (exclude "Future" planned templates)
        template_pattern = r"\| `(101\d{2}-TEMPLATE-[^`]+\.md)` \|[^|]+\| Active \|"
        indexed_templates = set(re.findall(template_pattern, content))

        # Check for missing entries (actual files not in "Active" index entries)
        missing = actual_templates - indexed_templates
        assert not missing, (
            "TEMPLATE INDEX DRIFT: Files exist but not in index:\n"
            + "\n".join(f"  - {f}" for f in sorted(missing))
            + "\n\nAdd these to docs/templates/10100-TEMPLATE-GUIDE.md"
        )

        # Note: We don't check for orphaned entries because the index
        # legitimately contains "Future" placeholders for planned templates

    def test_skill_instructions_index_complete(self) -> None:
        """Verify all skill instruction files are listed in 10600 index.

        Skill instructions are prompts/procedures for specific tasks.
        Missing entries mean skills that agents won't discover.
        """
        index_file = SKILLS_DIR / "10600-skill-instructions-index.md"

        # Skip if index doesn't exist yet (will be created)
        if not index_file.exists():
            return  # Index not yet created

        # Find actual skill instruction files
        actual_skills = {
            f.name
            for f in SKILLS_DIR.glob("106*-skill-*.md")
            if f.name != "10600-skill-instructions-index.md"
        }

        # Extract skills referenced in index (exclude the index file itself)
        content = index_file.read_text(encoding="utf-8")
        indexed_skills = extract_links_from_markdown(
            content, r"106\d{2}-skill-[^)]+\.md"
        )
        indexed_skills.discard("10600-skill-instructions-index.md")

        # Check for missing entries
        missing = actual_skills - indexed_skills
        assert not missing, (
            "SKILL INDEX DRIFT: Files exist but not in index:\n"
            + "\n".join(f"  - {f}" for f in sorted(missing))
            + "\n\nAdd these to docs/skills/10600-skill-instructions-index.md"
        )

        # Check for orphaned entries
        orphaned = indexed_skills - actual_skills
        assert not orphaned, (
            "SKILL INDEX DRIFT: Index references non-existent files:\n"
            + "\n".join(f"  - {f}" for f in sorted(orphaned))
            + "\n\nRemove these from docs/skills/10600-skill-instructions-index.md"
        )


class TestIndexCrossReferences:
    """Verify indexes don't have broken cross-references."""

    def test_adr_index_next_number_current(self) -> None:
        """Verify ADR index 'next available number' is accurate."""
        index_file = ADRS_DIR / "10200-ADR-index.md"
        content = index_file.read_text(encoding="utf-8")

        # Extract "next available number" from content
        match = re.search(r"next available number \(currently (\d+)\)", content)
        assert match, "ADR index missing 'next available number' statement"

        claimed_next = int(match.group(1))

        # Find highest actual ADR number
        adr_numbers = []
        for f in ADRS_DIR.glob("102*-ADR-*.md"):
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
