"""
Multi-line/Single-line PSV Reader for Stonex custodian files.

Handles three PSV variants:
1. SINGLE-LINE FIXED-WIDTH (e.g., Sal_pos.txt — 39 fields per line)
2. SINGLE-LINE VARIABLE-WIDTH (e.g., Sal_csh.txt — 45–58 fields per line)
3. MULTI-LINE (e.g., sal_act.txt with dashed-line separator;
   sal_rad.txt with blank-line separator)
"""

import re
from typing import List, Optional


def read_psv_file(file_path: str, mode: str = 'auto') -> List[List[str]]:
    """
    Read a PSV (pipe-separated values) file and return records as lists of fields.
    
    Args:
        file_path: Path to the PSV file
        mode: One of 'single_line', 'multi_line_dashed', 'multi_line_blank', 'auto'
    
    Returns:
        List of records, each record is a list of string fields
    
    Behavior:
        - For single_line: read each non-empty line, split on '|', return list of fields
        - For multi-line variants: detect record boundaries, concatenate physical lines
          into one logical line (joined with '|'), split on '|', return list of fields
        - Strip trailing whitespace on each field; don't strip leading whitespace
          inside fields (some descriptions have leading spaces)
        - Handle records of different lengths gracefully (don't assume fixed schema)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if mode == 'auto':
        mode = _detect_mode(content)
    
    if mode == 'single_line':
        return _read_single_line(content)
    elif mode == 'multi_line_dashed':
        return _read_multi_line_dashed(content)
    elif mode == 'multi_line_blank':
        return _read_multi_line_blank(content)
    else:
        raise ValueError(f"Unknown mode: {mode}")


def _detect_mode(content: str) -> str:
    """
    Auto-detect PSV variant based on file content.
    
    Rules:
    - If file contains lines matching r'^-{20,}$' → multi_line_dashed
    - Else if file contains 2+ consecutive newlines AND record count seems
      consistent with grouped lines → multi_line_blank
    - Else → single_line
    """
    lines = content.split('\n')
    
    # Check for dashed lines
    if any(re.match(r'^-{20,}$', line) for line in lines):
        return 'multi_line_dashed'
    
    # Check for blank lines (2+ consecutive newlines)
    if '\n\n' in content:
        # If we see a pattern of non-empty lines followed by blank lines, it's multi-line blank
        return 'multi_line_blank'
    
    # Default to single-line
    return 'single_line'


def _read_single_line(content: str) -> List[List[str]]:
    """Read single-line PSV format."""
    records = []
    for line in content.split('\n'):
        line = line.rstrip()  # Strip trailing whitespace
        if line:  # Skip empty lines
            fields = line.split('|')
            # Strip trailing whitespace on each field only
            fields = [f.rstrip() for f in fields]
            records.append(fields)
    return records


def _read_multi_line_dashed(content: str) -> List[List[str]]:
    """Read multi-line PSV format with dashed-line separators (e.g., sal_act.txt)."""
    records = []
    current_record_lines = []
    
    for line in content.split('\n'):
        line = line.rstrip()
        
        # Check if this is a separator line
        if re.match(r'^-{20,}$', line):
            # If we have accumulated lines, join them and add to records
            if current_record_lines:
                # Join lines with '|' to create one logical record
                logical_line = '|'.join(current_record_lines)
                # Split on '|' to get fields
                fields = logical_line.split('|')
                # Strip trailing whitespace on each field
                fields = [f.rstrip() for f in fields]
                records.append(fields)
                current_record_lines = []
        elif line:  # Non-empty, non-separator line
            current_record_lines.append(line)
    
    # Don't forget the last record if file doesn't end with separator
    if current_record_lines:
        logical_line = '|'.join(current_record_lines)
        fields = logical_line.split('|')
        fields = [f.rstrip() for f in fields]
        records.append(fields)
    
    return records


def _read_multi_line_blank(content: str) -> List[List[str]]:
    """Read multi-line PSV format with blank-line separators (e.g., sal_rad.txt)."""
    records = []
    
    # Split by blank lines (one or more consecutive newlines)
    # Group consecutive non-empty lines
    current_record_lines = []
    
    for line in content.split('\n'):
        line = line.rstrip()
        
        if line:  # Non-empty line
            current_record_lines.append(line)
        else:  # Empty line (record separator)
            if current_record_lines:
                # Join lines with '|' to create one logical record
                logical_line = '|'.join(current_record_lines)
                # Split on '|' to get fields
                fields = logical_line.split('|')
                # Strip trailing whitespace on each field
                fields = [f.rstrip() for f in fields]
                records.append(fields)
                current_record_lines = []
    
    # Don't forget the last record if file doesn't end with blank line
    if current_record_lines:
        logical_line = '|'.join(current_record_lines)
        fields = logical_line.split('|')
        fields = [f.rstrip() for f in fields]
        records.append(fields)
    
    return records


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python smart_reader.py <file_path> [mode]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'auto'
    
    records = read_psv_file(file_path, mode)
    
    print(f"File: {file_path}")
    print(f"Detected mode: {_detect_mode(open(file_path).read())}")
    print(f"Record count: {len(records)}")
    print()
    
    if records:
        print(f"First record ({len(records[0])} fields):")
        print(f"  {records[0][:10]}")  # First 10 fields
        print()
        
        if len(records) > 1:
            print(f"Second record ({len(records[1])} fields):")
            print(f"  {records[1][:10]}")  # First 10 fields
