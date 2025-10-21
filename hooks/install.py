#!/usr/bin/env python3
"""
Idempotent installer for Prompt Paladin Cursor hook.

Safely manages ~/.cursor/hooks.json with proper JSON parsing, backups,
and preservation of existing hooks from other projects.

Usage:
    python hooks/install.py              # Install hook
    python hooks/install.py --dry-run    # Preview changes
    python hooks/install.py --force      # Reinstall even if present
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.END} {msg}")


def get_project_root() -> Path:
    """Get the absolute path to the project root."""
    # This script is in hooks/, so project root is parent
    return Path(__file__).parent.parent.resolve()


def get_hooks_config_path() -> Path:
    """Get the path to ~/.cursor/hooks.json."""
    return Path.home() / ".cursor" / "hooks.json"


def load_hooks_config() -> Optional[Dict]:
    """
    Load existing hooks configuration.
    
    Returns:
        Dict if file exists and is valid JSON, None otherwise
    """
    config_path = get_hooks_config_path()
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Existing hooks.json is corrupted: {e}")
        print_info(f"Location: {config_path}")
        return None
    except Exception as e:
        print_error(f"Error reading hooks.json: {e}")
        return None


def create_backup(config_path: Path) -> Optional[Path]:
    """
    Create a timestamped backup of the hooks config.
    
    Returns:
        Path to backup file, or None if backup failed
    """
    if not config_path.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_suffix(f".backup.{timestamp}")
    
    try:
        import shutil
        shutil.copy2(config_path, backup_path)
        return backup_path
    except Exception as e:
        print_warning(f"Could not create backup: {e}")
        return None


def is_prompt_paladin_hook(hook: Dict, project_root: Path) -> bool:
    """
    Check if a hook configuration is for Prompt Paladin.
    
    Matches by checking if command or args contain the project path.
    """
    project_str = str(project_root)
    
    command = hook.get('command', '')
    args = hook.get('args', [])
    
    # Check if command contains project path
    if project_str in str(command):
        return True
    
    # Check if any arg contains project path
    for arg in args:
        if project_str in str(arg):
            return True
    
    return False


def find_prompt_paladin_hook(config: Dict, project_root: Path) -> Tuple[Optional[int], Optional[Dict]]:
    """
    Find Prompt Paladin hook in the config.
    
    Returns:
        (index, hook_dict) if found, (None, None) otherwise
    """
    hooks_list = config.get('hooks', {}).get('beforeSubmitPrompt', [])
    
    for idx, hook in enumerate(hooks_list):
        if is_prompt_paladin_hook(hook, project_root):
            return idx, hook
    
    return None, None


def create_hook_config(project_root: Path) -> Dict:
    """Create the hook configuration for Prompt Paladin."""
    # Use wrapper script instead of direct Python call
    # Direct Python call doesn't work reliably with Cursor's stdin handling
    hook_wrapper = project_root / "hooks" / "run.sh"
    
    return {
        "command": str(hook_wrapper)
    }


def hooks_are_equal(hook1: Dict, hook2: Dict) -> bool:
    """Check if two hook configs are functionally equivalent."""
    # With wrapper approach, only command matters
    return hook1.get('command') == hook2.get('command')


def install_hook(dry_run: bool = False, force: bool = False) -> int:
    """
    Install the Prompt Paladin hook.
    
    Returns:
        0 on success, 1 on error
    """
    project_root = get_project_root()
    config_path = get_hooks_config_path()
    
    print_info(f"Project root: {project_root}")
    print_info(f"Config file: {config_path}")
    print()
    
    # Verify wrapper script exists
    hook_wrapper = project_root / "hooks" / "run.sh"
    if not hook_wrapper.exists():
        print_error(f"Hook wrapper not found: {hook_wrapper}")
        print_info("The hooks/run.sh file is missing from the project")
        return 1
    
    # Verify .venv exists
    venv_python = project_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        print_error(f"Python venv not found: {venv_python}")
        print_info("Run 'uv sync' to create the virtual environment first")
        return 1
    
    # Load existing config or create new
    existing_config = load_hooks_config()
    
    if existing_config is None:
        # Create new config
        config = {
            "version": 1,
            "hooks": {
                "beforeSubmitPrompt": []
            }
        }
        print_info("No existing hooks.json found, will create new")
    else:
        config = existing_config
        # Ensure structure exists
        if 'hooks' not in config:
            config['hooks'] = {}
        if 'beforeSubmitPrompt' not in config['hooks']:
            config['hooks']['beforeSubmitPrompt'] = []
    
    # Check if already installed
    idx, existing_hook = find_prompt_paladin_hook(config, project_root)
    new_hook = create_hook_config(project_root)
    
    if idx is not None:
        # Already installed
        if hooks_are_equal(existing_hook, new_hook):
            if not force:
                print_success("Prompt Paladin hook is already installed")
                print_info("Use --force to reinstall")
                return 0
            else:
                print_info("Hook already installed, reinstalling due to --force")
                action = "reinstall"
        else:
            print_warning("Hook found with different paths, updating")
            action = "update"
        
        # Update existing hook
        config['hooks']['beforeSubmitPrompt'][idx] = new_hook
    else:
        # Install new hook
        print_info("Installing new hook")
        config['hooks']['beforeSubmitPrompt'].append(new_hook)
        action = "install"
    
    if dry_run:
        print()
        print_info("DRY RUN - No changes will be made")
        print()
        print("Would write to ~/.cursor/hooks.json:")
        print(json.dumps(config, indent=2))
        return 0
    
    # Create backup if file exists
    if config_path.exists():
        backup_path = create_backup(config_path)
        if backup_path:
            print_info(f"Backup created: {backup_path.name}")
    
    # Ensure ~/.cursor directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write config atomically (temp file + rename)
    temp_path = config_path.with_suffix('.tmp')
    try:
        with open(temp_path, 'w') as f:
            json.dump(config, f, indent=2)
            f.write('\n')  # Add trailing newline
        
        # Atomic rename
        temp_path.replace(config_path)
        
        print()
        if action == "install":
            print_success("Hook installed successfully!")
        elif action == "update":
            print_success("Hook updated successfully!")
        else:
            print_success("Hook reinstalled successfully!")
        
        print()
        print("Next steps:")
        print("1. Restart Cursor completely (Cmd+Q then reopen)")
        print("2. Submit a prompt to test")
        print()
        print("To uninstall: ./uninstall_hook.sh")
        
        return 0
        
    except Exception as e:
        print_error(f"Failed to write config: {e}")
        if temp_path.exists():
            temp_path.unlink()
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Install Prompt Paladin hook for Cursor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hooks/install.py              # Install hook
  python hooks/install.py --dry-run    # Preview changes
  python hooks/install.py --force      # Reinstall even if present
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Reinstall even if already installed'
    )
    
    args = parser.parse_args()
    
    try:
        sys.exit(install_hook(dry_run=args.dry_run, force=args.force))
    except KeyboardInterrupt:
        print()
        print_warning("Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

