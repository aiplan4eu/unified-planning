# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Build ENHSP into .planners/enhsp-20, where the `opt-pddl-planner` test engine looks for it.

`unified_planning/test/pddl/enhsp.py` registers that engine only if
`<repo-root>/.planners/enhsp-20/enhsp.jar` exists, and then runs it with `java -jar`. The
directory is gitignored, so this script is what puts the jar there -- both locally and, via
`just install-enhsp`, inside the install-enhsp composite action.

This is deliberately stdlib-only Python rather than shell: the justfile runs recipes through
cmd.exe on Windows (a bare `bash` there resolves to the WSL launcher), so a bash recipe could
not be shared with the Windows CI job.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEST = REPO_ROOT / ".planners" / "enhsp-20"
REPOSITORY = "https://gitlab.com/enricos83/ENHSP-Public.git"


def build(source: Path) -> None:
    """Reproduce upstream's ./compile, which is javac + jar + a copy of libs/.

    Inlining those steps rather than invoking ./compile is what keeps this script free of a
    bash dependency. It is safe because the tag is pinned by the caller; re-check this
    function against upstream's ./compile whenever that tag is bumped.
    """
    out = source / "out"
    out.mkdir(exist_ok=True)
    sources = sorted((source / "src").glob("*.java")) + sorted(
        (source / "src" / "planners").glob("*.java")
    )
    if not sources:
        sys.exit(f"error: no Java sources found under {source / 'src'}")
    subprocess.run(
        # "libs/*" is expanded by Java itself, not by a shell, so pass it through verbatim.
        ["javac", "-encoding", "utf8", "-d", "out", "-classpath", "libs/*"]
        + [str(path.relative_to(source)) for path in sources],
        cwd=source,
        check=True,
    )
    subprocess.run(
        [
            "jar",
            "--create",
            "--file",
            "enhsp.jar",
            "--manifest",
            "manifest.mf",
            "-C",
            "out/",
            ".",
        ],
        cwd=source,
        check=True,
    )


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"usage: {Path(__file__).name} <enhsp-tag>")
    tag = sys.argv[1]

    if (DEST / "enhsp.jar").is_file():
        print(
            f"ENHSP already built in {DEST}, skipping (remove that directory to rebuild)"
        )
        return

    missing = [tool for tool in ("git", "javac", "jar") if shutil.which(tool) is None]
    if missing:
        sys.exit(
            f"error: {', '.join(missing)} not found on PATH. "
            "Building ENHSP needs git and a JDK (CI uses 17)."
        )

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        source = Path(tmp) / "ENHSP-Public"
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", tag, REPOSITORY, str(source)],
            check=True,
        )
        build(source)
        DEST.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source / "libs", DEST / "libs", dirs_exist_ok=True)
        shutil.copy2(source / "enhsp.jar", DEST / "enhsp.jar")

    print(f"ENHSP {tag} built into {DEST}")


if __name__ == "__main__":
    main()
