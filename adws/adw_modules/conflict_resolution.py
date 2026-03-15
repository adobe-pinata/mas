"""
Conflict resolution module for append-only files in ADWS workflows.

This module provides automatic conflict resolution for known append-only files
that commonly conflict during parallel workflow execution. It detects conflicts,
applies file-specific merge strategies, and enables Zero Touch Execution (ZTE)
for parallel ADWS workflows.
"""

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable


# Exception classes for conflict resolution errors
class ConflictResolutionError(Exception):
    """Base exception for conflict resolution errors."""
    pass


class UnknownFileConflictError(ConflictResolutionError):
    """Raised when a conflict occurs in a non-append-only file."""
    pass


class MergeStrategyError(ConflictResolutionError):
    """Raised when a merge strategy fails to resolve a conflict."""
    pass


class FileParsingError(ConflictResolutionError):
    """Raised when parsing a conflicting file fails."""
    pass


@dataclass
class AppendOnlyFile:
    """Configuration for an append-only file that supports auto-resolution."""

    path: str
    description: str
    merge_strategy: Callable[[str, logging.Logger], None]


def detect_merge_conflicts(repo_root: str, logger: logging.Logger) -> List[str]:
    """
    Detect merge conflicts in the working directory.

    Args:
        repo_root: Path to the repository root
        logger: Logger instance

    Returns:
        List of file paths with conflicts

    Example:
        >>> conflicts = detect_merge_conflicts("/path/to/repo", logger)
        >>> conflicts
        ['.claude/commands/conditional_docs.md', 'app_docs/agentic_kpis.md']
    """
    try:
        # Run git status to find conflicting files
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            check=True
        )

        conflicting_files = []
        for line in result.stdout.split('\n'):
            if line.startswith('UU '):  # Unmerged, both modified
                file_path = line[3:].strip()
                conflicting_files.append(file_path)
                logger.debug(f"Detected conflict in: {file_path}")

        logger.info(f"Found {len(conflicting_files)} conflicting file(s)")
        return conflicting_files

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to detect conflicts: {e}")
        raise ConflictResolutionError(f"Git status failed: {e.stderr}")


def is_append_only_file(file_path: str, append_only_files: Dict[str, AppendOnlyFile]) -> bool:
    """
    Check if a file is in the known append-only list.

    Args:
        file_path: Relative path to the file
        append_only_files: Dictionary of append-only file configurations

    Returns:
        True if the file is append-only, False otherwise

    Example:
        >>> is_append_only_file('.claude/commands/conditional_docs.md', APPEND_ONLY_FILES)
        True
        >>> is_append_only_file('src/main.py', APPEND_ONLY_FILES)
        False
    """
    return file_path in append_only_files


def get_conflict_sections(file_path: str, logger: logging.Logger) -> Tuple[str, str, str]:
    """
    Extract conflict sections from a file with merge conflict markers.

    Args:
        file_path: Path to the conflicting file
        logger: Logger instance

    Returns:
        Tuple of (ours_content, theirs_content, base_content)

    Raises:
        FileParsingError: If conflict markers are not found or malformed

    Example:
        >>> ours, theirs, base = get_conflict_sections('.claude/commands/conditional_docs.md', logger)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by conflict markers
        # Format: <<<<<<< HEAD\n{ours}\n=======\n{theirs}\n>>>>>>> branch\n
        conflict_pattern = re.compile(
            r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> .*?\n',
            re.DOTALL
        )

        matches = conflict_pattern.findall(content)
        if not matches:
            raise FileParsingError(f"No conflict markers found in {file_path}")

        # For simplicity, we'll handle single conflict section
        # Multiple conflicts in same file will be handled iteratively
        if len(matches) > 1:
            logger.warning(f"Multiple conflict sections in {file_path}, will process all")

        # Extract non-conflicting parts (before first conflict, between conflicts, after last)
        parts = conflict_pattern.split(content)

        return content, matches, parts

    except Exception as e:
        logger.error(f"Failed to parse conflict sections in {file_path}: {e}")
        raise FileParsingError(f"Could not parse {file_path}: {e}")


def resolve_conditional_docs_conflict(file_path: str, logger: logging.Logger) -> None:
    """
    Resolve conflicts in .claude/commands/conditional_docs.md.

    This file has a simple structure: header, instructions, and a list of
    documentation entries. We merge by keeping both versions' entries,
    removing duplicates, and sorting alphabetically.

    Args:
        file_path: Path to the conflicting file
        logger: Logger instance

    Raises:
        MergeStrategyError: If merge fails

    Example:
        >>> resolve_conditional_docs_conflict('.claude/commands/conditional_docs.md', logger)
    """
    logger.info(f"Resolving conditional_docs.md conflict in: {file_path}")

    backup_path = f"{file_path}.backup"

    try:
        # Read the full file with conflict markers
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise MergeStrategyError(f"File not found: {file_path}")
        except IOError as e:
            raise MergeStrategyError(f"Cannot read file {file_path}: {e}")

        # Create backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Created backup at: {backup_path}")

        # Extract sections
        conflict_pattern = re.compile(
            r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> .*?\n',
            re.DOTALL
        )

        matches = conflict_pattern.findall(content)
        if not matches:
            raise MergeStrategyError(f"No conflict markers found in {file_path}")

        # Extract documentation entries from both versions
        # Each entry is a filename line plus its optional Conditions block
        ours_entries = {}  # Use dict to preserve entry blocks: {filename: full_block}
        theirs_entries = {}

        def extract_entry_blocks(section_text):
            """Extract complete entry blocks (filename + conditions) from section."""
            entries = {}
            lines = section_text.split('\n')
            current_entry = []
            current_filename = None

            for line in lines:
                # Check if this is a filename line (starts with "- " and contains ".md")
                if line.strip().startswith('- ') and '.md' in line:
                    # Save previous entry if exists
                    if current_filename and current_entry:
                        entries[current_filename] = '\n'.join(current_entry)
                    # Start new entry
                    current_filename = line.strip()
                    current_entry = [line]
                elif current_entry:
                    # This is part of current entry (conditions, etc.)
                    current_entry.append(line)

            # Save last entry
            if current_filename and current_entry:
                entries[current_filename] = '\n'.join(current_entry)

            return entries

        for ours_section, theirs_section in matches:
            ours_entries.update(extract_entry_blocks(ours_section))
            theirs_entries.update(extract_entry_blocks(theirs_section))

        # Merge entries (theirs overwrites ours for same filename)
        all_entries_dict = {**ours_entries, **theirs_entries}

        # Sort by filename and get full blocks
        all_entries = [all_entries_dict[key] for key in sorted(all_entries_dict.keys())]
        logger.info(f"Merging {len(ours_entries)} + {len(theirs_entries)} entries = {len(all_entries)} unique entries")

        # Reconstruct the file
        # Remove conflict markers and replace with merged entries
        merged_content = conflict_pattern.sub('', content)

        # Find the insertion point (after "## Conditional Documentation" section)
        # and insert all merged entries
        insertion_marker = "## Conditional Documentation\n"
        if insertion_marker in merged_content:
            parts = merged_content.split(insertion_marker, 1)
            # Keep everything after the marker until we hit entries
            after_marker = parts[1]

            # Find where entries start (first "- " line)
            lines = after_marker.split('\n')
            header_lines = []
            for i, line in enumerate(lines):
                if line.strip().startswith('- ') and '.md' in line:
                    break
                header_lines.append(line)

            # Rebuild content
            # all_entries now contains multi-line blocks, join with newlines
            merged_content = (
                parts[0] +
                insertion_marker +
                '\n'.join(header_lines) +
                '\n' +
                '\n'.join(all_entries) +
                '\n'
            )
        else:
            raise MergeStrategyError(f"Could not find insertion point in {file_path}")

        # Write merged content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(merged_content)

        logger.info(f"✅ Successfully resolved conditional_docs.md conflict")
        logger.debug(f"Merged {len(all_entries)} documentation entries")

    except Exception as e:
        logger.error(f"Failed to resolve conditional_docs.md conflict: {e}")
        # Restore from backup if it exists
        if os.path.exists(backup_path):
            with open(backup_path, 'r', encoding='utf-8') as f:
                with open(file_path, 'w', encoding='utf-8') as out:
                    out.write(f.read())
            logger.info("Restored from backup")
        raise MergeStrategyError(f"Conditional docs merge failed: {e}")


def resolve_agentic_kpis_conflict(file_path: str, logger: logging.Logger) -> None:
    """
    Resolve conflicts in app_docs/agentic_kpis.md.

    This file contains two markdown tables:
    1. Summary metrics (Current Streak, Longest Streak, etc.)
    2. Detailed ADW KPIs table with one row per workflow

    We merge by:
    1. Combining all rows from both versions (keeping unique ADW IDs)
    2. Sorting by date and ADW ID
    3. Recalculating summary metrics from the merged data

    Args:
        file_path: Path to the conflicting file
        logger: Logger instance

    Raises:
        MergeStrategyError: If merge fails

    Example:
        >>> resolve_agentic_kpis_conflict('app_docs/agentic_kpis.md', logger)
    """
    logger.info(f"Resolving agentic_kpis.md conflict in: {file_path}")

    backup_path = f"{file_path}.backup"

    try:
        # Read the full file with conflict markers
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise MergeStrategyError(f"File not found: {file_path}")
        except IOError as e:
            raise MergeStrategyError(f"Cannot read file {file_path}: {e}")

        # Create backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Created backup at: {backup_path}")

        # Extract sections
        conflict_pattern = re.compile(
            r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> .*?\n',
            re.DOTALL
        )

        matches = conflict_pattern.findall(content)
        if not matches:
            raise MergeStrategyError(f"No conflict markers found in {file_path}")

        # Extract ADW KPI rows from both versions
        ours_rows = {}
        theirs_rows = {}

        for ours_section, theirs_section in matches:
            # Extract table rows (lines starting with "|" that have ADW ID)
            for line in ours_section.split('\n'):
                if line.strip().startswith('|') and '|' in line[1:]:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4 and parts[2]:  # Has ADW ID
                        adw_id = parts[2]
                        ours_rows[adw_id] = line.strip()

            for line in theirs_section.split('\n'):
                if line.strip().startswith('|') and '|' in line[1:]:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4 and parts[2]:  # Has ADW ID
                        adw_id = parts[2]
                        theirs_rows[adw_id] = line.strip()

        # Merge rows (theirs overwrites ours if same ADW ID)
        all_rows = {**ours_rows, **theirs_rows}

        # Parse rows for sorting and metric calculation
        parsed_rows = []
        for row in all_rows.values():
            parts = [p.strip() for p in row.split('|')]
            if len(parts) >= 4:
                parsed_rows.append({
                    'date': parts[1],
                    'adw_id': parts[2],
                    'issue_number': parts[3] if len(parts) > 3 else '',
                    'issue_class': parts[4] if len(parts) > 4 else '',
                    'attempts': parts[5] if len(parts) > 5 else '',
                    'plan_size': parts[6] if len(parts) > 6 else '',
                    'diff_size': parts[7] if len(parts) > 7 else '',
                    'created': parts[8] if len(parts) > 8 else '',
                    'updated': parts[9] if len(parts) > 9 else '',
                    'raw': row
                })

        # Sort by date (descending) and ADW ID
        parsed_rows.sort(key=lambda x: (x['date'], x['adw_id']))

        logger.info(f"Merging {len(ours_rows)} + {len(theirs_rows)} rows = {len(parsed_rows)} unique rows")

        # Recalculate summary metrics
        summary = calculate_kpi_summary(parsed_rows, logger)

        # Reconstruct the file
        # Find the file structure
        header_match = re.search(r'(.*?## Agentic KPIs\n.*?\n)', content, re.DOTALL)
        if not header_match:
            raise MergeStrategyError("Could not find '## Agentic KPIs' header")

        header = header_match.group(1)

        # Build summary table
        timestamp = datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')
        summary_table = f"""| Metric            | Value          | Last Updated             |
| ----------------- | -------------- | ------------------------ |
| Current Streak    | {summary['current_streak']} | {timestamp} |
| Longest Streak    | {summary['longest_streak']} | {timestamp} |
| Total Plan Size   | {summary['total_plan_size']} lines     | {timestamp} |
| Largest Plan Size | {summary['largest_plan_size']} lines      | {timestamp} |
| Total Diff Size   | {summary['total_diff_size']} lines    | {timestamp} |
| Largest Diff Size | {summary['largest_diff_size']} lines    | {timestamp} |
| Average Presence  | {summary['average_presence']:.2f}           | {timestamp} |
"""

        # Build detail table
        detail_header = """
## ADW KPIs

Detailed metrics for individual ADW workflow runs.

| Date       | ADW ID   | Issue Number | Issue Class | Attempts | Plan Size (lines) | Diff Size (Added/Removed/Files) | Created                      | Updated                      |
| ---------- | -------- | ------------ | ----------- | -------- | ----------------- | ------------------------------- | ---------------------------- | ---------------------------- |
"""

        detail_rows = '\n'.join([row['raw'] for row in parsed_rows])

        merged_content = header + summary_table + detail_header + detail_rows + '\n'

        # Write merged content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(merged_content)

        logger.info(f"✅ Successfully resolved agentic_kpis.md conflict")
        logger.debug(f"Merged {len(parsed_rows)} KPI rows, recalculated summary metrics")
        logger.debug(f"Summary: streak={summary['current_streak']}, total_diff={summary['total_diff_size']}")

    except Exception as e:
        logger.error(f"Failed to resolve agentic_kpis.md conflict: {e}")
        # Restore from backup if it exists
        if os.path.exists(backup_path):
            with open(backup_path, 'r', encoding='utf-8') as f:
                with open(file_path, 'w', encoding='utf-8') as out:
                    out.write(f.read())
            logger.info("Restored from backup")
        raise MergeStrategyError(f"Agentic KPIs merge failed: {e}")


def calculate_kpi_summary(rows: List[Dict], logger: logging.Logger) -> Dict[str, any]:
    """
    Calculate summary metrics from merged KPI rows.

    Args:
        rows: List of parsed KPI row dictionaries
        logger: Logger instance

    Returns:
        Dictionary with summary metrics

    Example:
        >>> summary = calculate_kpi_summary(rows, logger)
        >>> summary
        {'current_streak': 25, 'longest_streak': 25, 'total_plan_size': 6991, ...}
    """
    try:
        if not rows:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_plan_size': 0,
                'largest_plan_size': 0,
                'total_diff_size': 0,
                'largest_diff_size': 0,
                'average_presence': 0.0
            }

        # Current streak: consecutive workflows with attempts = 1
        current_streak = 0
        for row in reversed(rows):  # Start from most recent
            attempts = int(row['attempts']) if row['attempts'].isdigit() else 0
            if attempts == 1:
                current_streak += 1
            else:
                break

        # Longest streak: longest sequence of attempts = 1
        longest_streak = 0
        current = 0
        for row in rows:
            attempts = int(row['attempts']) if row['attempts'].isdigit() else 0
            if attempts == 1:
                current += 1
                longest_streak = max(longest_streak, current)
            else:
                current = 0

        # Total and largest plan size
        total_plan_size = 0
        largest_plan_size = 0
        for row in rows:
            plan_size = int(row['plan_size']) if row['plan_size'].isdigit() else 0
            total_plan_size += plan_size
            largest_plan_size = max(largest_plan_size, plan_size)

        # Total and largest diff size (parse "added/removed/files" format)
        total_diff_size = 0
        largest_diff_size = 0
        for row in rows:
            diff_match = re.match(r'(\d+)/(\d+)/(\d+)', row['diff_size'])
            if diff_match:
                added = int(diff_match.group(1))
                removed = int(diff_match.group(2))
                diff_total = added + removed
                total_diff_size += diff_total
                largest_diff_size = max(largest_diff_size, diff_total)

        # Average presence (attempts)
        total_attempts = sum(int(row['attempts']) if row['attempts'].isdigit() else 0 for row in rows)
        average_presence = total_attempts / len(rows) if rows else 0.0

        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_plan_size': total_plan_size,
            'largest_plan_size': largest_plan_size,
            'total_diff_size': total_diff_size,
            'largest_diff_size': largest_diff_size,
            'average_presence': average_presence
        }

    except Exception as e:
        logger.error(f"Failed to calculate KPI summary: {e}")
        raise MergeStrategyError(f"Summary calculation failed: {e}")


# Registry of append-only files with their merge strategies
APPEND_ONLY_FILES: Dict[str, AppendOnlyFile] = {
    '.claude/commands/conditional_docs.md': AppendOnlyFile(
        path='.claude/commands/conditional_docs.md',
        description='Conditional documentation index with conditions for when to read each doc',
        merge_strategy=resolve_conditional_docs_conflict
    ),
    'app_docs/agentic_kpis.md': AppendOnlyFile(
        path='app_docs/agentic_kpis.md',
        description='Agentic KPI tracking table with workflow performance metrics',
        merge_strategy=resolve_agentic_kpis_conflict
    )
}


def auto_resolve_conflicts(
    repo_root: str,
    conflicting_files: List[str],
    logger: logging.Logger
) -> Tuple[bool, List[str], List[str]]:
    """
    Automatically resolve conflicts in known append-only files.

    Args:
        repo_root: Path to the repository root
        conflicting_files: List of files with conflicts
        logger: Logger instance

    Returns:
        Tuple of (all_resolved, resolved_files, unresolved_files)

    Raises:
        UnknownFileConflictError: If conflicts exist in non-append-only files
        MergeStrategyError: If auto-resolution fails

    Example:
        >>> success, resolved, unresolved = auto_resolve_conflicts('/path/to/repo', conflicts, logger)
        >>> if success:
        ...     print(f"Resolved {len(resolved)} files")
    """
    logger.info(f"Attempting to auto-resolve {len(conflicting_files)} conflicting file(s)")

    resolved_files = []
    unresolved_files = []

    # Check if all conflicting files are append-only
    for file_path in conflicting_files:
        if not is_append_only_file(file_path, APPEND_ONLY_FILES):
            logger.warning(f"Conflict in non-append-only file: {file_path}")
            unresolved_files.append(file_path)

    if unresolved_files:
        logger.error(f"Cannot auto-resolve: {len(unresolved_files)} non-append-only file(s) have conflicts")
        raise UnknownFileConflictError(
            f"Conflicts exist in non-append-only files: {', '.join(unresolved_files)}"
        )

    # Resolve each append-only file
    for file_path in conflicting_files:
        try:
            full_path = os.path.join(repo_root, file_path)
            config = APPEND_ONLY_FILES[file_path]

            logger.info(f"Resolving {config.description}: {file_path}")
            config.merge_strategy(full_path, logger)

            resolved_files.append(file_path)
            logger.info(f"✅ Resolved: {file_path}")

        except Exception as e:
            logger.error(f"Failed to resolve {file_path}: {e}")
            unresolved_files.append(file_path)
            raise MergeStrategyError(f"Auto-resolution failed for {file_path}: {e}")

    all_resolved = len(unresolved_files) == 0
    logger.info(f"Auto-resolution complete: {len(resolved_files)} resolved, {len(unresolved_files)} failed")

    return all_resolved, resolved_files, unresolved_files
