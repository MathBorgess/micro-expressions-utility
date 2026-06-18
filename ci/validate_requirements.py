#!/usr/bin/env python3
"""Valida que toda dependência DIRETA do `pyproject.toml` está na allowlist aprovada.

Gate do Harness (REQ-010): bibliotecas fora da allowlist reprovam o build. Adições
exigem aprovação explícita e atualização desta lista.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ALLOWLIST: frozenset[str] = frozenset(
    {
        # runtime
        "fastapi",
        "uvicorn",
        "python-multipart",
        "sqlmodel",
        "pydantic-settings",
        "httpx",
        "opencv-python",
        "mediapipe",
        "faster-whisper",
        "tiktoken",
        "psutil",
        "numpy",
        # dev / harness
        "ruff",
        "mypy",
        "pytest",
        "pytest-cov",
        "pytest-asyncio",
        "memory-profiler",
    }
)


def _normalize(requirement: str) -> str:
    """Extrai o nome canônico de uma spec (ex.: 'uvicorn[standard]>=0.34' -> 'uvicorn')."""
    name = re.split(r"[<>=!~;\[\s]", requirement, maxsplit=1)[0]
    return name.strip().lower().replace("_", "-")


def collect_direct_dependencies(pyproject_path: Path) -> set[str]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    specs: list[str] = []
    project = data.get("project", {})
    specs.extend(d for d in project.get("dependencies", []) if isinstance(d, str))
    for group in project.get("optional-dependencies", {}).values():
        if isinstance(group, list):
            specs.extend(d for d in group if isinstance(d, str))
    for group in data.get("dependency-groups", {}).values():
        if isinstance(group, list):
            specs.extend(d for d in group if isinstance(d, str))
    return {_normalize(spec) for spec in specs}


def main() -> int:
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    names = collect_direct_dependencies(pyproject_path)
    unauthorized = sorted(names - ALLOWLIST)
    if unauthorized:
        print("[validate_requirements] DEPENDÊNCIAS NÃO AUTORIZADAS:")
        for name in unauthorized:
            print(f"  - {name}")
        print("Atualize a allowlist (com aprovação) ou remova a dependência.")
        return 1
    print(f"[validate_requirements] OK — {len(names)} dependências diretas, todas autorizadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
