"""Robust software version parsing and semantic comparison for Windows packages."""

import re
from typing import Optional, Tuple
from packaging.version import InvalidVersion
from packaging.version import parse as pep440_parse
from winget_updater.utils.logger import get_logger

logger = get_logger()


def clean_version_string(ver: str) -> str:
    """Cleans up common non-semantic artifacts from version strings."""
    if not ver:
        return ""
    v = ver.strip()
    # Strip leading 'v' or 'V' if followed by a digit
    if (v.startswith("v") or v.startswith("V")) and len(v) > 1 and v[1].isdigit():
        v = v[1:]
    # Strip trailing build hashes if separated by '+' or '-'
    v = re.sub(r"\+.*$", "", v)
    return v


def parse_fallback_tuple(ver: str) -> Tuple:
    """Fallback parser for non-PEP 440 version strings (e.g., date formats, hex revisions)."""
    cleaned = clean_version_string(ver)
    parts = re.split(r"[.\-_]", cleaned)
    tuple_parts = []
    for p in parts:
        if not p:
            continue
        if p.isdigit():
            tuple_parts.append(int(p))
        else:
            # Separate digits from alpha characters (e.g. '10b' -> (10, 'b'))
            sub_parts = re.findall(r"\d+|\D+", p)
            for sp in sub_parts:
                if sp.isdigit():
                    tuple_parts.append(int(sp))
                else:
                    tuple_parts.append(sp.lower())
    return tuple(tuple_parts)


def compare_versions(v1_str: Optional[str], v2_str: Optional[str]) -> Optional[int]:
    """Compares two version strings.
    
    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
        None if either version is missing or indeterminate.
    """
    if not v1_str or not v2_str:
        return None

    s1 = clean_version_string(v1_str)
    s2 = clean_version_string(v2_str)

    if not s1 or not s2 or s1.lower() == "unknown" or s2.lower() == "unknown":
        return None

    if s1.lower() == s2.lower():
        return 0

    # Try standard PEP 440 parsing first
    try:
        pv1 = pep440_parse(s1)
        pv2 = pep440_parse(s2)
        if pv1 < pv2:
            return -1
        elif pv1 > pv2:
            return 1
        else:
            return 0
    except (InvalidVersion, TypeError):
        pass

    # Fallback to tuple-based comparison
    try:
        t1 = parse_fallback_tuple(s1)
        t2 = parse_fallback_tuple(s2)

        # Pad shorter tuple with 0 if both are integer-dominant
        max_len = max(len(t1), len(t2))
        padded1 = list(t1) + [0] * (max_len - len(t1))
        padded2 = list(t2) + [0] * (max_len - len(t2))

        for p1, p2 in zip(padded1, padded2):
            # If types differ, convert both to string for comparison
            if type(p1) is not type(p2):
                p1, p2 = str(p1), str(p2)
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
        return 0
    except Exception as e:
        logger.debug(f"Version comparison fallback failed for '{v1_str}' vs '{v2_str}': {e}")
        return None

