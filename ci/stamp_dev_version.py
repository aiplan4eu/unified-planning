"""Stamp a derived dev version into pyproject.toml.

Run only in CI on master-branch builds. The patched pyproject.toml is consumed
by the downstream build / dev-release step but is never committed.

Version (PEP 440):  <base>.dev<N>+g<sha>    e.g. 1.3.0.dev512+gabc1234

<N> is the total commit count on HEAD (monotonic, tag-independent) and <sha>
the short commit hash, so every master build gets a unique, ordered version.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys


def sh(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def main() -> None:
    pyproject = pathlib.Path("pyproject.toml")
    text = pyproject.read_text()

    match = re.search(r'^version = "(\d+\.\d+\.\d+)"', text, flags=re.MULTILINE)
    if match is None:
        sys.exit(
            "refusing to stamp: a plain 'X.Y.Z' version was not found in "
            "pyproject.toml (already suffixed?)"
        )
    base = match.group(1)

    n = sh("git", "rev-list", "--count", "HEAD")
    sha = sh("git", "rev-parse", "--short=7", "HEAD")
    dev_version = f"{base}.dev{n}+g{sha}"

    pyproject.write_text(
        re.sub(
            r'^version = ".*"',
            f'version = "{dev_version}"',
            text,
            count=1,
            flags=re.MULTILINE,
        )
    )
    print(f"stamped version = {dev_version}")


if __name__ == "__main__":
    main()
