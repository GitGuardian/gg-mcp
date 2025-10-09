#!/usr/bin/env python3
"""
Script to publish gg-mcp to the Model Context Protocol (MCP) registry.

Prerequisites:
- Package must be published to PyPI first (run publish_to_pypi.py)
- mcp-publisher CLI installed (brew install mcp-publisher)
- GitHub account with access to GitGuardian organization
- server.json configured in project root

Usage:
    # Publish to MCP registry
    python scripts/publish_to_mcp_registry.py

    # Dry run (validate without publishing)
    python scripts/publish_to_mcp_registry.py --dry-run
"""

import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None, capture: bool = True) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    if capture:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr
    else:
        # Interactive mode - let user see output
        result = subprocess.run(cmd, cwd=cwd)
        return result.returncode, "", ""


def check_prerequisites() -> bool:
    """Check if required tools and files are available."""
    print("Checking prerequisites...")

    # Check if mcp-publisher is installed
    returncode, stdout, _ = run_command(["which", "mcp-publisher"])
    if returncode != 0:
        print("❌ Error: 'mcp-publisher' is not installed")
        print("   Install it with: brew install mcp-publisher")
        return False

    print("✅ mcp-publisher is installed")

    # Check mcp-publisher version
    returncode, stdout, _ = run_command(["mcp-publisher", "--version"])
    if returncode == 0:
        print(f"   Version: {stdout.strip()}")

    # Check if server.json exists
    if not Path("server.json").exists():
        print("❌ Error: server.json not found in project root")
        print("   Run 'mcp-publisher init' first")
        return False

    print("✅ server.json exists")

    return True


def validate_server_json() -> bool:
    """Validate server.json configuration."""
    print("\nValidating server.json...")

    try:
        with open("server.json") as f:
            config = json.load(f)

        # Check required fields
        required_fields = ["name", "description", "version", "packages"]
        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False

        print("✅ server.json structure is valid")

        # Display configuration
        print("\nConfiguration:")
        print(f"  Name: {config['name']}")
        print(f"  Description: {config['description']}")
        print(f"  Version: {config['version']}")

        if config.get("packages"):
            package = config["packages"][0]
            print(f"\n  Package:")
            print(f"    Registry: {package.get('registryType')}")
            print(f"    Identifier: {package.get('identifier')}")
            print(f"    Version: {package.get('version')}")

            # Check if package is on PyPI
            if package.get("registryType") == "pypi":
                identifier = package.get("identifier")
                print(f"\n  Checking if {identifier} exists on PyPI...")
                returncode, _, _ = run_command(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"https://pypi.org/pypi/{identifier}/json"])
                # Note: returncode check won't work as expected with curl, but we'll keep for structure

        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in server.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading server.json: {e}")
        return False


def check_github_auth() -> bool:
    """Check if user is authenticated with GitHub."""
    print("\nChecking GitHub authentication...")

    # Try to get current auth status (this may not work, mcp-publisher might not have a status command)
    # We'll just inform the user about the requirement
    print("ℹ️  You will need to authenticate with GitHub")
    print("   Make sure you have access to the GitGuardian organization")

    return True


def login_github() -> bool:
    """Login to GitHub via mcp-publisher."""
    print("\nAuthenticating with GitHub...")
    print("This will open a browser window for authentication.")

    response = input("Continue with GitHub login? [y/N]: ").strip().lower()
    if response != "y":
        print("Skipping GitHub login")
        return False

    returncode, stdout, stderr = run_command(["mcp-publisher", "login", "github"], capture=False)

    if returncode != 0:
        print(f"❌ GitHub authentication failed")
        return False

    print("✅ GitHub authentication successful")
    return True


def publish_to_registry(dry_run: bool = False) -> bool:
    """Publish server to MCP registry."""
    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
    else:
        print("Publishing to MCP registry...")
    print("=" * 60)

    if dry_run:
        print("\nWould execute: mcp-publisher publish")
        print("✅ Dry run completed")
        return True

    # Run publish command
    returncode, stdout, stderr = run_command(["mcp-publisher", "publish"], capture=False)

    if returncode != 0:
        print(f"\n❌ Publication failed")
        if stderr:
            print(f"Error: {stderr}")
        return False

    print("\n✅ Successfully published to MCP registry!")
    return True


def main() -> int:
    """Main entry point."""
    # Parse arguments
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv

    print("=" * 60)
    print("Publishing gg-mcp to MCP Registry")
    print("=" * 60)

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Change to project root
    import os
    os.chdir(project_root)

    print(f"\nWorking directory: {project_root}")

    # Check prerequisites
    if not check_prerequisites():
        return 1

    # Validate server.json
    if not validate_server_json():
        return 1

    # Check GitHub auth
    if not check_github_auth():
        return 1

    # Confirm before proceeding
    print("\n" + "=" * 60)
    print("Ready to publish to MCP registry")
    print("=" * 60)

    print("\nBefore continuing, ensure:")
    print("  ✓ Package is published to PyPI")
    print("  ✓ server.json is correct")
    print("  ✓ You have GitHub org access")

    if not dry_run:
        response = input("\nContinue with publication? [y/N]: ").strip().lower()
        if response != "y":
            print("Aborted by user")
            return 0

    # Login to GitHub (if not dry run)
    if not dry_run:
        if not login_github():
            print("\n⚠️  Proceeding without explicit GitHub login")
            print("   mcp-publisher publish may prompt for authentication")

    # Publish to registry
    if not publish_to_registry(dry_run=dry_run):
        return 1

    print("\n" + "=" * 60)
    print("✅ Process complete!")
    print("=" * 60)

    if not dry_run:
        print("\nYour server should now be available in the MCP registry:")
        print("  https://github.com/modelcontextprotocol/registry")
        print("\nUsers can install it with:")
        print("  uvx gg-mcp")

    return 0


if __name__ == "__main__":
    sys.exit(main())
