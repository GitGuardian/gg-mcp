#!/usr/bin/env python3
"""
Script to publish gg-mcp to PyPI.

Prerequisites:
- PyPI account at https://pypi.org/account/register/
- PyPI API token from https://pypi.org/manage/account/token/
- Set token in environment: export PYPI_TOKEN="your-token"
  OR use interactive mode (will prompt for token)

Usage:
    # Interactive mode (prompts for token)
    python scripts/publish_to_pypi.py

    # Using environment variable
    export PYPI_TOKEN="pypi-..."
    python scripts/publish_to_pypi.py

    # Test on TestPyPI first
    python scripts/publish_to_pypi.py --test
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def check_prerequisites() -> bool:
    """Check if required tools are available."""
    print("Checking prerequisites...")

    # Check if uv is installed
    returncode, _, _ = run_command(["which", "uv"])
    if returncode != 0:
        print("❌ Error: 'uv' is not installed")
        print("   Install it from: https://docs.astral.sh/uv/getting-started/installation/")
        return False

    print("✅ uv is installed")
    return True


def clean_dist() -> None:
    """Remove existing dist directory."""
    dist_dir = Path("dist")
    if dist_dir.exists():
        print(f"Cleaning {dist_dir}...")
        shutil.rmtree(dist_dir)


def build_package() -> bool:
    """Build the package using uv."""
    print("\nBuilding package...")
    returncode, stdout, stderr = run_command(["uv", "build"])

    if returncode != 0:
        print(f"❌ Build failed:\n{stderr}")
        return False

    print("✅ Package built successfully")

    # List built files
    dist_dir = Path("dist")
    if dist_dir.exists():
        files = list(dist_dir.glob("*"))
        print("\nBuilt files:")
        for file in files:
            print(f"  - {file.name}")

    return True


def upload_to_pypi(test: bool = False) -> bool:
    """Upload package to PyPI or TestPyPI."""
    # Check for token
    token = os.environ.get("PYPI_TOKEN" if not test else "TEST_PYPI_TOKEN")

    if not token:
        print(f"\n{'TestPyPI' if test else 'PyPI'} token not found in environment.")
        token = input(f"Enter your {'TestPyPI' if test else 'PyPI'} API token: ").strip()

        if not token:
            print("❌ No token provided. Aborting.")
            return False

    # Prepare twine command
    cmd = ["uv", "run", "twine", "upload"]

    if test:
        cmd.extend(["--repository", "testpypi"])

    cmd.append("dist/*")

    # Set up environment with token
    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = token

    print(f"\nUploading to {'TestPyPI' if test else 'PyPI'}...")

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Upload failed:\n{result.stderr}")
        return False

    print(f"✅ Successfully uploaded to {'TestPyPI' if test else 'PyPI'}!")

    # Show verification instructions
    if test:
        print("\nVerify installation with:")
        print("  uvx --index-url https://test.pypi.org/simple/ gg-mcp")
        print("\nView on TestPyPI:")
        print("  https://test.pypi.org/project/gg-mcp/")
    else:
        print("\nVerify installation with:")
        print("  uvx gg-mcp")
        print("\nView on PyPI:")
        print("  https://pypi.org/project/gg-mcp/")

    return True


def main() -> int:
    """Main entry point."""
    # Parse arguments
    test_mode = "--test" in sys.argv or "-t" in sys.argv

    print("=" * 60)
    print(f"Publishing gg-mcp to {'TestPyPI' if test_mode else 'PyPI'}")
    print("=" * 60)

    # Check prerequisites
    if not check_prerequisites():
        return 1

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    print(f"\nWorking directory: {project_root}")

    # Clean previous builds
    clean_dist()

    # Build package
    if not build_package():
        return 1

    # Confirm upload
    print(f"\n{'⚠️  TEST MODE: ' if test_mode else ''}Ready to upload to {'TestPyPI' if test_mode else 'PyPI'}")
    response = input("Continue? [y/N]: ").strip().lower()

    if response != "y":
        print("Aborted by user")
        return 0

    # Upload to PyPI
    if not upload_to_pypi(test=test_mode):
        return 1

    print("\n" + "=" * 60)
    print("✅ Publication complete!")
    print("=" * 60)

    if not test_mode:
        print("\nNext step: Register with MCP registry")
        print("  python scripts/publish_to_mcp_registry.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
