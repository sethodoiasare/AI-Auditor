"""
JSON parsing and output formatting utilities.
"""

import json
import re
from pathlib import Path
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


def load_prompt(name: str) -> str:
    """
    Load a prompt template from the prompts/ directory.

    Args:
        name: Prompt file name without extension (e.g., 'auditor').

    Returns:
        Prompt text content.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / f"{name}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _extract_json_object(text: str) -> str | None:
    """Extract the first balanced JSON object from the text."""
    start = None
    depth = 0
    in_string = False
    escape = False

    for idx, char in enumerate(text):
        if start is None:
            if char == "{":
                start = idx
                depth = 1
                in_string = False
                escape = False
            continue

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start: idx + 1]

    return None


def _parse_key_value_lines(text: str) -> dict | None:
    """Parse a series of bare key/value lines into a dictionary."""
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("-") or line.startswith("*"):
            line = line.lstrip("-* ")
        match = re.match(r'"?([a-zA-Z0-9_]+)"?\s*:\s*(.*)', line)
        if not match:
            continue
        key, raw_value = match.groups()
        raw_value = raw_value.strip().rstrip(',')
        if not raw_value:
            continue
        if raw_value.startswith('"') and raw_value.endswith('"'):
            data[key] = raw_value[1:-1]
            continue
        if raw_value.lower() in {"true", "false", "null"}:
            try:
                data[key] = json.loads(raw_value.lower())
                continue
            except json.JSONDecodeError:
                pass
        if raw_value.startswith("[") or raw_value.startswith("{"):
            try:
                data[key] = json.loads(raw_value)
                continue
            except json.JSONDecodeError:
                pass
        if raw_value.isdigit():
            data[key] = int(raw_value)
            continue
        try:
            data[key] = float(raw_value)
            continue
        except ValueError:
            pass
        data[key] = raw_value
    return data if data else None


def parse_json_response(text: str) -> dict:
    """
    Robustly parse a JSON object from Claude's response text.

    Handles raw JSON, markdown code blocks (```json ... ```, ``` ... ```),
    and bare JSON objects embedded in prose.

    Args:
        text: Raw response text from Claude.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If no valid JSON object can be extracted.
    """
    stripped = text.strip()

    # 1. Try direct parse
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 2. Try extracting from ```json ... ``` code block
    match = re.search(r"```json\s*(.*?)\s*```", stripped, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Try extracting from ``` ... ``` code block (no language tag)
    match = re.search(r"```\s*(.*?)\s*```", stripped, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 4. Try finding a balanced JSON object in the text
    json_text = _extract_json_object(stripped)
    if json_text:
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass

    # 5. Try reconstructing a bare JSON object when the model drops the outer braces
    if stripped.lstrip().startswith('"'):
        candidate = "{" + stripped.strip()
        if not candidate.endswith("}"):
            candidate += "}"
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 6. Try parsing key/value lines directly
    key_value_data = _parse_key_value_lines(stripped)
    if key_value_data is not None:
        return key_value_data

    logger.error("Failed to parse Claude response as JSON. Raw response: %s", text[:2000])
    raise ValueError(
        f"Could not parse a valid JSON object from response. "
        f"First 300 chars: {text[:300]!r}"
    )


def parse_json_list(text: str) -> list:
    """
    Robustly parse a JSON array from Claude's response text.

    Args:
        text: Raw response text from Claude.

    Returns:
        Parsed list, or empty list if nothing valid is found.
    """
    stripped = text.strip()

    # 1. Direct parse
    try:
        result = json.loads(stripped)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # 2. Code block extraction
    for pattern in [r"```json\s*(.*?)\s*```", r"```\s*(.*?)\s*```"]:
        match = re.search(pattern, stripped, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

    # 3. Bare array in text
    match = re.search(r"\[.*?\]", stripped, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []


def format_output(data: dict, indent: int = 2) -> str:
    """
    Pretty-print a dictionary as formatted JSON.

    Args:
        data: Dictionary to format.
        indent: JSON indentation level.

    Returns:
        Formatted JSON string.
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)
