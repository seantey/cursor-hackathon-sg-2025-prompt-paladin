#!/usr/bin/env python3
"""
Idempotent uninstaller for Prompt Paladin Cursor hook.

Safely removes only Prompt Paladin's hook from ~/.cursor/hooks.json
while preserving hooks from other projects.

Usage:
    python hooks/uninstall.py              # Uninstall hook
    python hooks/uninstall.py --dry-run    # Preview changes
    python hooks/uninstall.py --keep-empty # Keep file even if empty
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


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


def has_other_hooks(config: Dict) -> bool:
    """Check if there are any other hooks besides beforeSubmitPrompt."""
    hooks = config.get('hooks', {})
    
    # Check for other hook types
    for key in hooks:
        if key != 'beforeSubmitPrompt' and hooks[key]:
            return True
    
    return False


def uninstall_hook(dry_run: bool = False, keep_empty: bool = False) -> int:
    """
    Uninstall the Prompt Paladin hook.
    
    Returns:
        0 on success, 1 on error
    """
    project_root = get_project_root()
    config_path = get_hooks_config_path()
    
    print_info(f"Project root: {project_root}")
    print_info(f"Config file: {config_path}")
    print()
    
    # Check if config exists
    if not config_path.exists():
        print_info("No hooks.json file found - hook is not installed")
        return 0
    
    # Load config
    config = load_hooks_config()
    if config is None:
        print_error("Could not load hooks.json")
        return 1
    
    # Find Prompt Paladin hook
    before_submit_hooks = config.get('hooks', {}).get('beforeSubmitPrompt', [])
    
    # Find all non-Prompt-Paladin hooks
    other_hooks = [
        hook for hook in before_submit_hooks
        if not is_prompt_paladin_hook(hook, project_root)
    ]
    
    # Check if hook was found
    if len(other_hooks) == len(before_submit_hooks):
        print_info("Prompt Paladin hook is not installed")
        return 0
    
    num_removed = len(before_submit_hooks) - len(other_hooks)
    print_info(f"Found {num_removed} Prompt Paladin hook(s) to remove")
    
    if dry_run:
        print()
        print_info("DRY RUN - No changes will be made")
        print()
        if other_hooks:
            print("Would keep these hooks:")
            for hook in other_hooks:
                print(f"  - {hook.get('command', 'unknown')}")
        else:
            if has_other_hooks(config):
                print("Would keep hooks.json (has other hook types)")
            elif keep_empty:
                print("Would keep empty hooks.json")
            else:
                print("Would delete hooks.json (no remaining hooks)")
        return 0
    
    # Create backup
    backup_path = create_backup(config_path)
    if backup_path:
        print_info(f"Backup created: {backup_path.name}")
    
    # Update config
    if other_hooks:
        # Keep file with remaining hooks
        config['hooks']['beforeSubmitPrompt'] = other_hooks
        
        try:
            temp_path = config_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(config, f, indent=2)
                f.write('\n')
            
            temp_path.replace(config_path)
            
            print()
            print_success("Hook uninstalled successfully!")
            print_info(f"Preserved {len(other_hooks)} other hook(s)")
            
        except Exception as e:
            print_error(f"Failed to write config: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return 1
    
    elif has_other_hooks(config) or keep_empty:
        # Keep file but remove beforeSubmitPrompt hooks
        config['hooks']['beforeSubmitPrompt'] = []
        
        # Clean up empty beforeSubmitPrompt array if no other hooks
        if not has_other_hooks(config) and not keep_empty:
            if 'beforeSubmitPrompt' in config['hooks']:
                del config['hooks']['beforeSubmitPrompt']
        
        try:
            temp_path = config_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(config, f, indent=2)
                f.write('\n')
            
            temp_path.replace(config_path)
            
            print()
            print_success("Hook uninstalled successfully!")
            print_info("Kept hooks.json file")
            
        except Exception as e:
            print_error(f"Failed to write config: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return 1
    
    else:
        # Delete file (no remaining hooks)
        try:
            config_path.unlink()
            print()
            print_success("Hook uninstalled successfully!")
            print_info("Deleted hooks.json (no remaining hooks)")
            
        except Exception as e:
            print_error(f"Failed to delete config: {e}")
            return 1
    
    print()
    print("Next steps:")
    print("1. Restart Cursor completely (Cmd+Q then reopen)")
    print()
    print("To reinstall: ./install_hook.sh")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Uninstall Prompt Paladin hook from Cursor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hooks/uninstall.py              # Uninstall hook
  python hooks/uninstall.py --dry-run    # Preview changes
  python hooks/uninstall.py --keep-empty # Keep file even if empty
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--keep-empty',
        action='store_true',
        help='Keep hooks.json even if no hooks remain'
    )
    
    args = parser.parse_args()
    
    try:
        sys.exit(uninstall_hook(dry_run=args.dry_run, keep_empty=args.keep_empty))
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

