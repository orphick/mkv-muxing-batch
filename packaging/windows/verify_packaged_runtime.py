"""Reject native DLLs that shadow the Windows runtime used by Qt."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SYSTEM_ICU_PATTERN = re.compile(r"icu(?:uc|in|dt)\d*\.dll", re.IGNORECASE)


def find_shadowing_icu_dlls(application_directory: Path) -> list[Path]:
    """Return top-level ICU DLLs that would override Windows System32 ICU."""
    internal = application_directory / "_internal"
    if not internal.is_dir():
        raise FileNotFoundError(f"Packaged runtime directory not found: {internal}")
    return sorted(
        path
        for path in internal.iterdir()
        if path.is_file() and SYSTEM_ICU_PATTERN.fullmatch(path.name)
    )


def verify(application_directory: Path, qt_major: int = 6) -> list[str]:
    errors: list[str] = []
    internal = application_directory / "_internal"
    if qt_major == 6:
        required_qt_files = (
            internal / "PySide6" / "QtCore.pyd",
            internal / "PySide6" / "Qt6Core.dll",
            internal / "PySide6" / "pyside6.abi3.dll",
            internal / "shiboken6" / "shiboken6.abi3.dll",
        )
        forbidden_binding = internal / "PySide2"
    elif qt_major == 5:
        required_qt_files = (
            internal / "PySide2" / "QtCore.pyd",
            internal / "PySide2" / "Qt5Core.dll",
            internal / "PySide2" / "pyside2.abi3.dll",
            internal / "shiboken2" / "shiboken2.abi3.dll",
        )
        forbidden_binding = internal / "PySide6"
    else:
        raise ValueError(f"Unsupported Qt major version: {qt_major}")
    errors.extend(
        f"Required Qt runtime file is missing: {path}"
        for path in required_qt_files
        if not path.is_file()
    )
    if forbidden_binding.exists():
        errors.append(f"Unexpected Qt binding was packaged: {forbidden_binding}")
    if qt_major == 6:
        errors.extend(
            f"Shadowing ICU DLL must not be packaged: {path}"
            for path in find_shadowing_icu_dlls(application_directory)
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("application_directory", type=Path)
    parser.add_argument("--qt-major", choices=(5, 6), default=6, type=int)
    args = parser.parse_args()
    errors = verify(args.application_directory.resolve(), qt_major=args.qt_major)
    if errors:
        print("Packaged runtime verification failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"Packaged Qt {args.qt_major} runtime verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
