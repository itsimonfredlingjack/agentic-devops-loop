#!/usr/bin/env python3
"""
PreToolUse Security Hook

Validates tool usage before execution to prevent:
1. Unauthorized package installations
2. Modifications to security-critical files
3. Dangerous shell commands (injection vectors)

Exit codes:
- 0: Allow tool execution
- 2: Block tool execution (with reason in stderr)
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Allowed packages - add your project's dependencies here
ALLOWED_NPM_PACKAGES = {
    # Testing
    "jest", "mocha", "chai", "vitest", "playwright", "@playwright/test",
    # Linting
    "eslint", "prettier", "typescript", "@types/*",
    # Common utilities
    "lodash", "axios", "express", "fastify",
    # Build tools
    "vite", "esbuild", "webpack", "rollup",
}

ALLOWED_PIP_PACKAGES = {
    # Testing
    "pytest", "pytest-cov", "pytest-asyncio", "coverage",
    # Linting
    "ruff", "black", "mypy", "flake8",
    # Common utilities
    "requests", "httpx", "fastapi", "flask", "pydantic",
    # Build tools
    "build", "wheel", "setuptools",
}

# Paths that cannot be written to
PROTECTED_PATHS = [
    ".github/",
    ".claude/hooks/",
    ".githooks/",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env",
]

# Dangerous shell patterns
DANGEROUS_PATTERNS = [
    r"curl\s+.*\|\s*(bash|sh|zsh)",           # curl | bash
    r"wget\s+.*\|\s*(bash|sh|zsh)",           # wget | bash
    r"\beval\s*\(",                            # eval()
    r"\beval\s+",                              # eval command
    r">\s*/etc/",                              # Write to /etc
    r"rm\s+-rf\s+/",                           # rm -rf /
    r"rm\s+-rf\s+\*",                          # rm -rf *
    r":\(\)\s*\{\s*:\|:&\s*\}",               # Fork bomb
    r"mkfs\.",                                 # Format filesystem
    r"dd\s+if=.*of=/dev/",                    # Direct disk write
    r"chmod\s+777",                            # Overly permissive
    r"chmod\s+\+s",                            # Setuid
    r"sudo\s+",                                # Sudo commands
    r"su\s+-",                                 # Switch user
    r">/dev/sd",                               # Write to disk
    r"\$\(.*\)",                               # Command substitution (careful)
    r"`.*`",                                   # Backtick execution
    r"nc\s+-l",                                # Netcat listener
    r"python.*-c\s*['\"].*exec",              # Python exec
    r"node.*-e\s*['\"].*child_process",       # Node child_process
    r"base64\s+-d.*\|.*sh",                   # Encoded payload execution
]

# Commands that need extra scrutiny
SENSITIVE_COMMANDS = [
    "npm install",
    "npm i ",
    "yarn add",
    "pnpm add",
    "pip install",
    "pip3 install",
    "poetry add",
]

PIP_VERSION_PATTERN = re.compile(r"(==|>=|<=|~=|!=|>|<)")


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def _normalize_allowlist(raw) -> Dict[str, List[str]]:
    """Normalize allowlist entries into a dict of name -> [versions]."""
    if isinstance(raw, dict):
        normalized = {}
        for name, versions in raw.items():
            if isinstance(versions, list):
                normalized[name] = [str(v) for v in versions]
            elif isinstance(versions, str):
                normalized[name] = [versions]
            else:
                normalized[name] = ["*"]
        return normalized
    if isinstance(raw, list):
        return {str(name): ["*"] for name in raw}
    return {}


def load_custom_allowlist():
    """Load project-specific package allowlist if exists."""
    allowlist_path = Path.cwd() / ".claude" / "package-allowlist.json"
    if allowlist_path.exists():
        with open(allowlist_path) as f:
            custom = json.load(f)
            policy = custom.get("policy", {})
            return (
                _normalize_allowlist(custom.get("npm", [])),
                _normalize_allowlist(custom.get("pip", [])),
                policy,
            )
    return {}, {}, {}


def _merge_allowlists(base_set: set, custom: Dict[str, List[str]]) -> Dict[str, List[str]]:
    allowlist = {name: ["*"] for name in base_set}
    allowlist.update(custom)
    return allowlist


def _resolve_allowed_versions(pkg_name: str, allowlist: Dict[str, List[str]]) -> Optional[List[str]]:
    if pkg_name in allowlist:
        return allowlist[pkg_name]
    for pattern, versions in allowlist.items():
        if "*" in pattern:
            prefix = pattern.split("*", 1)[0]
            if pkg_name.startswith(prefix):
                return versions
    return None


def _parse_npm_spec(spec: str) -> Tuple[Optional[str], Optional[str]]:
    spec = spec.strip()
    if not spec or spec.startswith("-"):
        return None, None
    if spec.startswith(("file:", "git:", "git+")) or "://" in spec or spec.endswith(".tgz"):
        return None, None

    name = spec
    version = None

    if spec.startswith("@"):
        slash_index = spec.find("/")
        at_index = spec.rfind("@")
        if at_index > slash_index:
            name = spec[:at_index]
            version = spec[at_index + 1:] or None
    else:
        at_index = spec.rfind("@")
        if at_index > 0:
            name = spec[:at_index]
            version = spec[at_index + 1:] or None

    return name, version


def _parse_pip_spec(spec: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    spec = spec.strip()
    if not spec or spec.startswith("-"):
        return None, None, None
    if spec.startswith(("file:", "git+", "http://", "https://")) or "://" in spec:
        return None, None, None

    match = PIP_VERSION_PATTERN.search(spec)
    if match:
        name_part = spec[:match.start()]
        op = match.group(1)
        version = spec[match.end():] or None
    else:
        name_part = spec
        op = None
        version = None

    name = name_part.split("[", 1)[0]
    return name, op, version


def _is_pinned_npm_version(version: Optional[str]) -> bool:
    if not version:
        return False
    if version in {"latest", "next"}:
        return False
    if re.search(r"[~^<>*|]", version):
        return False
    return bool(re.match(r"^\d+(\.\d+){0,2}([\-+][0-9A-Za-z.-]+)?$", version))


def _is_pinned_pip_version(op: Optional[str], version: Optional[str]) -> bool:
    if op != "==" or not version:
        return False
    return "*" not in version


def validate_package_install(command: str) -> tuple[bool, str]:
    """Validate npm/pip install commands against allowlist."""
    custom_npm, custom_pip, policy = load_custom_allowlist()
    allowed_npm = _merge_allowlists(ALLOWED_NPM_PACKAGES, custom_npm)
    allowed_pip = _merge_allowlists(ALLOWED_PIP_PACKAGES, custom_pip)
    require_pinned = bool(policy.get("require_pinned_versions", False))

    # Extract package names from command
    if "npm install" in command or "npm i " in command or "yarn add" in command:
        # npm install package1 package2 --save-dev
        parts = command.split()
        packages = [p for p in parts if not p.startswith("-") and p not in
                   ["npm", "install", "i", "yarn", "add", "pnpm"]]

        for pkg in packages:
            pkg_name, version = _parse_npm_spec(pkg)
            if not pkg_name:
                return False, f"Unsupported npm spec '{pkg}'. Use registry packages only."

            allowed_versions = _resolve_allowed_versions(pkg_name, allowed_npm)
            if not allowed_versions:
                return False, f"Package '{pkg_name}' not in allowlist. Add to .claude/package-allowlist.json"

            if require_pinned and not _is_pinned_npm_version(version):
                return False, f"Package '{pkg_name}' must be installed with a pinned version (e.g., {pkg_name}@1.2.3)"

            if "*" not in allowed_versions:
                if not version:
                    allowed = ", ".join(allowed_versions)
                    return False, f"Package '{pkg_name}' requires a pinned version from allowlist: {allowed}"
                if version not in allowed_versions:
                    allowed = ", ".join(allowed_versions)
                    return False, f"Version '{version}' for '{pkg_name}' is not in allowlist: {allowed}"

    elif "pip install" in command or "pip3 install" in command or "poetry add" in command:
        parts = command.split()
        packages = [p for p in parts if not p.startswith("-") and p not in
                   ["pip", "pip3", "install", "poetry", "add"]]

        for pkg in packages:
            pkg_name, op, version = _parse_pip_spec(pkg)
            if not pkg_name:
                return False, f"Unsupported pip spec '{pkg}'. Use registry packages only."

            allowed_versions = _resolve_allowed_versions(pkg_name, allowed_pip)
            if not allowed_versions:
                return False, f"Package '{pkg_name}' not in allowlist. Add to .claude/package-allowlist.json"

            if require_pinned and not _is_pinned_pip_version(op, version):
                return False, f"Package '{pkg_name}' must be installed with a pinned version (e.g., {pkg_name}==1.2.3)"

            if "*" not in allowed_versions:
                if not version:
                    allowed = ", ".join(allowed_versions)
                    return False, f"Package '{pkg_name}' requires a pinned version from allowlist: {allowed}"
                if version not in allowed_versions:
                    allowed = ", ".join(allowed_versions)
                    return False, f"Version '{version}' for '{pkg_name}' is not in allowlist: {allowed}"

    return True, ""


def validate_file_path(path: str, operation: str) -> tuple[bool, str]:
    """Check if file path is protected."""
    path_lower = path.lower()

    for protected in PROTECTED_PATHS:
        if path_lower.startswith(protected.lower()) or f"/{protected.lower()}" in path_lower:
            return False, f"Cannot {operation} protected path: {protected}"

    return True, ""


def validate_shell_command(command: str) -> tuple[bool, str]:
    """Check for dangerous shell patterns."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Blocked dangerous pattern: {pattern}"

    return True, ""


def validate_tool_use(tool_name: str, tool_input: dict) -> tuple[bool, str]:
    """Main validation logic for tool usage."""

    # Bash/Shell commands
    if tool_name.lower() in ["bash", "shell", "execute"]:
        command = tool_input.get("command", "")

        # Check for dangerous patterns
        is_safe, reason = validate_shell_command(command)
        if not is_safe:
            return False, reason

        # Check package installations
        for sensitive in SENSITIVE_COMMANDS:
            if sensitive in command.lower():
                is_allowed, reason = validate_package_install(command)
                if not is_allowed:
                    return False, reason

    # File write operations
    elif tool_name.lower() in ["write", "edit", "create_file", "write_file"]:
        file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
        is_allowed, reason = validate_file_path(file_path, "write to")
        if not is_allowed:
            return False, reason

    # File delete operations
    elif tool_name.lower() in ["delete", "remove", "rm"]:
        file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
        is_allowed, reason = validate_file_path(file_path, "delete")
        if not is_allowed:
            return False, reason

    return True, ""


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main hook logic."""
    try:
        # Read input from stdin
        input_data = sys.stdin.read()

        if not input_data.strip():
            sys.exit(0)  # No input, allow

        try:
            hook_input = json.loads(input_data)
        except json.JSONDecodeError:
            sys.exit(0)  # Invalid JSON, fail open

        tool_name = hook_input.get("tool_name", "")
        tool_input = hook_input.get("tool_input", {})

        # Validate
        is_allowed, reason = validate_tool_use(tool_name, tool_input)

        if is_allowed:
            sys.exit(0)
        else:
            response = {
                "blocked": True,
                "reason": reason,
                "tool": tool_name,
                "suggestion": "Review the command and try an alternative approach"
            }
            json.dump(response, sys.stderr)
            sys.exit(2)

    except Exception as e:
        # Fail open on errors to prevent stuck state
        error_response = {"error": str(e), "action": "allow_on_error"}
        json.dump(error_response, sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
