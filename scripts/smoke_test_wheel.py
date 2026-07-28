from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> None:
    print("+", subprocess.list2cmdline(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _copy_source(destination: Path) -> None:
    ignored = shutil.ignore_patterns(
        ".git",
        ".venv",
        ".pytest_cache",
        "__pycache__",
        "*.egg-info",
        "*.pyc",
        "build",
        "dist",
    )
    shutil.copytree(REPO_ROOT, destination, ignore=ignored)


def _venv_paths(venv_dir: Path) -> tuple[Path, Path]:
    if os.name == "nt":
        scripts_dir = venv_dir / "Scripts"
        return scripts_dir / "python.exe", scripts_dir / "fms19.exe"
    scripts_dir = venv_dir / "bin"
    return scripts_dir / "python", scripts_dir / "fms19"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="fms19-wheel-smoke-") as temp_dir:
        root = Path(temp_dir)
        source_copy = root / "source"
        wheel_dir = root / "wheel"
        venv_dir = root / "venv"
        outside_dir = root / "outside-repository"
        wheel_dir.mkdir()
        outside_dir.mkdir()
        _copy_source(source_copy)

        _run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--outdir",
                str(wheel_dir),
                str(source_copy),
            ],
            cwd=outside_dir,
        )
        wheels = sorted(wheel_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"expected one wheel, found: {wheels}")

        venv.EnvBuilder(with_pip=True).create(venv_dir)
        venv_python, fms19 = _venv_paths(venv_dir)
        installed_env = os.environ.copy()
        installed_env.pop("PYTHONHOME", None)
        installed_env.pop("PYTHONPATH", None)
        installed_env["PYTHONNOUSERSITE"] = "1"
        installed_env["VIRTUAL_ENV"] = str(venv_dir)
        installed_env["PATH"] = (
            f"{fms19.parent}{os.pathsep}{installed_env.get('PATH', '')}"
        )

        _run(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                str(wheels[0]),
            ],
            cwd=outside_dir,
            env=installed_env,
        )

        for filename in ("server-script-ir.json", "server-script-ir-v2.json"):
            shutil.copy2(REPO_ROOT / "examples" / filename, outside_dir / filename)

        _run(
            [str(fms19), "validate-ir", "server-script-ir-v2.json"],
            cwd=outside_dir,
            env=installed_env,
        )
        schema_check = "\n".join(
            [
                "from pathlib import Path",
                "import sysconfig",
                "from fms19_toolkit.script_ir import _locate_schema_path, load_schema",
                "load_schema(2)",
                "actual = _locate_schema_path(2).resolve()",
                "expected = (",
                "    Path(sysconfig.get_path('data'))",
                "    / 'share'",
                "    / 'fms19-script-toolkit'",
                "    / 'schemas'",
                "    / 'script-ir-v2.schema.json'",
                ").resolve()",
                "if actual != expected:",
                "    raise SystemExit(f'wheel schema path mismatch: {actual} != {expected}')",
                "print(f'Installed schema: {actual}')",
            ]
        )
        _run(
            [str(venv_python), "-c", schema_check],
            cwd=outside_dir,
            env=installed_env,
        )
        _run(
            [
                str(fms19),
                "migrate-ir",
                "server-script-ir.json",
                "migrated-ir-v2.json",
            ],
            cwd=outside_dir,
            env=installed_env,
        )
        _run(
            [str(fms19), "validate-ir", "migrated-ir-v2.json"],
            cwd=outside_dir,
            env=installed_env,
        )

    print("Wheel smoke test passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
