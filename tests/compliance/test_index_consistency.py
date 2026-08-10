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


# Issue #829: ONE pattern per document type, used by BOTH discovery and index
# extraction.
#
# These previously diverged: discovery used a shell glob (`108*-audit-*.md`)
# while extraction used a regex (`108\d{2}-audit-...`). The glob is far more
# permissive — it matched `10833-wiki-audit-and-refresh-plan.md`, whose
# `-audit-` sits mid-name — but the regex requires `-audit-` immediately after
# the two-digit serial, so that file could never be matched in the index.
#
# The result was a test demanding an index entry it would then refuse to
# recognise: unfixable by editing the index, and it failed on main. Because the
# fleet dependabot gate exonerates a PR only when its failure set equals base's,
# an unstable red main deferred every open dependency bump (#804, #805, #809).
#
# Keeping discovery and extraction on a single pattern makes that divergence
# unrepresentable.
ADR_PATTERN = r"102\d{2}-ADR-[^)]+\.md"
AUDIT_PATTERN = r"108\d{2}-audit-[^)]+\.md"
SKILL_PATTERN = r"106\d{2}-skill-[^)]+\.md"
TEMPLATE_PATTERN = r"101\d{2}-TEMPLATE-[^`]+\.md"


def discover_documents(
    directory: Path, name_pattern: str, index_filename: str
) -> set[str]:
    """Find files whose full name matches `name_pattern`.

    Deliberately regex-based rather than glob-based so it can share the exact
    pattern used to extract entries from the index.

    Args:
        directory: Directory to scan.
        name_pattern: Regex the whole filename must match.
        index_filename: The index itself, excluded from results.

    Returns:
        Set of matching filenames.
    """
    regex = re.compile(name_pattern)
    return {
        f.name
        for f in directory.iterdir()
        if f.is_file() and regex.fullmatch(f.name) and f.name != index_filename
    }


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
        actual_adrs = discover_documents(ADRS_DIR, ADR_PATTERN, "10200-ADR-index.md")

        # Extract ADRs referenced in index
        content = index_file.read_text(encoding="utf-8")
        indexed_adrs = extract_links_from_markdown(content, ADR_PATTERN)

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
        actual_audits = discover_documents(
            AUDITS_DIR, AUDIT_PATTERN, "10800-audit-index.md"
        )

        # Extract audits referenced in index (section 10.1 has the links)
        content = index_file.read_text(encoding="utf-8")
        indexed_audits = extract_links_from_markdown(content, AUDIT_PATTERN)

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
        actual_templates = discover_documents(
            TEMPLATES_DIR, TEMPLATE_PATTERN, "10100-TEMPLATE-GUIDE.md"
        )

        # Extract templates referenced in index
        content = index_file.read_text(encoding="utf-8")

        # Templates are listed as `filename.md` in table cells
        # Match patterns like: | `10101-TEMPLATE-issue.md` |
        # Only match templates marked as "Active" (exclude "Future" planned templates)
        template_pattern = rf"\| `({TEMPLATE_PATTERN})` \|[^|]+\| Active \|"
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
        actual_skills = discover_documents(
            SKILLS_DIR, SKILL_PATTERN, "10600-skill-instructions-index.md"
        )

        # Extract skills referenced in index (exclude the index file itself)
        content = index_file.read_text(encoding="utf-8")
        indexed_skills = extract_links_from_markdown(content, SKILL_PATTERN)
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


class TestAuditDiscoveryScope:
    """Issue #829: what counts as an indexable audit.

    Discovery previously used a shell glob (``108*-audit-*.md``) while
    extraction used a regex (``108\\d{2}-audit-...``). The glob swept in files
    whose ``-audit-`` sits mid-name, which the regex could never match in the
    index — so the suite demanded index entries it would then refuse to
    recognise. That is unfixable by editing the index, and it failed on main.

    Because the fleet dependabot gate exonerates a PR only when its failure set
    equals base's, a red main deferred every open dependency bump.

    These tests pin the *scope* of discovery from both directions: too
    permissive re-admits the artifacts below, too strict silently stops
    enforcing the index at all.
    """

    def test_infix_artifacts_are_not_treated_as_indexable_audits(self) -> None:
        """Reports and plans about an audit are not themselves audits.

        `10833-wiki-audit-and-refresh-plan.md` and
        `10834-wiki-audit-report-2026-06.md` are a one-time plan and its report
        — outputs of the recurring `10817-audit-wiki-alignment.md`, by 10833's
        own statement. They are not schedulable audits, so the index (whose
        purpose is "audits that will be scheduled or run") must not require
        them.

        The old shell glob swept them in because `-audit-` appears mid-name.
        """
        discovered = discover_documents(AUDITS_DIR, AUDIT_PATTERN, "10800-audit-index.md")

        for artifact in (
            "10833-wiki-audit-and-refresh-plan.md",
            "10834-wiki-audit-report-2026-06.md",
        ):
            if (AUDITS_DIR / artifact).exists():
                assert artifact not in discovered, (
                    f"{artifact} was discovered as an indexable audit. "
                    "It is an output artifact, not a recurring audit definition."
                )

    def test_conventionally_named_audits_are_still_discovered(self) -> None:
        """The tightened pattern must not silently stop enforcing the index."""
        discovered = discover_documents(AUDITS_DIR, AUDIT_PATTERN, "10800-audit-index.md")

        # Guard against the fix "working" by discovering nothing at all.
        assert len(discovered) >= 20, (
            f"Only {len(discovered)} audits discovered; the pattern is too strict "
            "and the index is no longer being enforced."
        )
        assert "10809-audit-security.md" in discovered
        assert "10817-audit-wiki-alignment.md" in discovered


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
