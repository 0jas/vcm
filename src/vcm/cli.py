#!/usr/bin/env python3
"""
Version Control CLI - A command-line interface for Git semantic versioning operations.

This script provides CLI access to VersionControlManager functionality for managing
Git tags with semantic versioning patterns.
"""

import argparse
import sys
import os

try:
    from .vcm import VersionControlManager
except ImportError:
    # Fallback for direct execution
    from vcm import VersionControlManager


def get_repo_path():
    """Get the repository path, defaulting to current directory."""
    return os.getcwd()


def handle_get_current_tag(args):
    """Handle get_current_tag command."""
    repo_path = getattr(args, 'repo_path', get_repo_path())
    vcm = VersionControlManager(repo_path)
    try:
        result = vcm.get_current_tag(
            prerelease_tag=args.prerelease_tag,
            production=args.production
        )
        if not result:
            print("No matching tags found in repository", file=sys.stderr)
            return 1

        if args.detailed:
            if args.production:
                print(f"Latest production tag found: {result}")
            else:
                print(f"Latest {args.prerelease_tag} prerelease tag found: {result}")
        else:
            print(result)
        return 0
    except Exception as e:
        print(f"Error getting current tag: {e}", file=sys.stderr)
        return 1


def handle_increment_prerelease(args):
    """Handle increment_prerelease_tag command."""
    repo_path = getattr(args, 'repo_path', get_repo_path())
    vcm = VersionControlManager(repo_path)
    try:
        result = vcm.increment_prerelease_tag(
            tag=args.tag,
            prerelease_tag=args.prerelease_tag,
            major_bump=args.major_bump
        )
        if args.detailed:
            print(f"Created prerelease tag: {result}")
        else:
            print(result)
        return 0
    except ValueError as e:
        print(f"Error: Invalid tag format - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error creating prerelease tag: {e}", file=sys.stderr)
        return 1


def handle_init_new_rc(args):
    """Handle init_new_rc command."""
    repo_path = getattr(args, 'repo_path', get_repo_path())
    vcm = VersionControlManager(repo_path)
    try:
        result = vcm.init_new_rc(prerelease_tag=args.prerelease_tag)
        if result:
            if args.detailed:
                print(f"Created initial RC tag: {result}")
            else:
                print(result)
            return 0
        else:
            print("No development tag found to create RC from", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error creating RC tag: {e}", file=sys.stderr)
        return 1


def handle_init_new_patch(args):
    """Handle init_new_patch command."""
    repo_path = getattr(args, 'repo_path', get_repo_path())
    vcm = VersionControlManager(repo_path)
    try:
        result = vcm.init_new_patch()
        if result:
            if args.detailed:
                print(f"Created initial patch tag: {result}")
            else:
                print(result)
            return 0
        else:
            print("No production tag found to create patch from", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error creating patch tag: {e}", file=sys.stderr)
        return 1


def handle_get_current_rc_patch(args):
    """Handle get_current_rc_patch command."""
    repo_path = getattr(args, 'repo_path', get_repo_path())
    vcm = VersionControlManager(repo_path)
    try:
        result = vcm.get_current_rc_patch(
            tag=args.tag,
            prerelease_tag=args.prerelease_tag
        )
        if result:
            print(result)
            return 0
        else:
            print(f"No {args.prerelease_tag} tag found for version {args.tag}", file=sys.stderr)
            return 1
    except ValueError as e:
        print(f"Error: Invalid tag format - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error getting current tag: {e}", file=sys.stderr)
        return 1


def handle_increment_rc_patch(args):
    """Handle increment_rc_patch command."""
    repo_path = getattr(args, 'repo_path', get_repo_path())
    vcm = VersionControlManager(repo_path)
    try:
        result = vcm.increment_rc_patch(
            tag=args.tag,
            prerelease_tag=args.prerelease_tag
        )
        if result:
            if args.detailed:
                print(f"Created incremented {args.prerelease_tag} tag: {result}")
            else:
                print(result)
            return 0
        else:
            print(f"No existing {args.prerelease_tag} tag found to increment", file=sys.stderr)
            return 1
    except ValueError as e:
        print(f"Error: Invalid tag format - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error incrementing {args.prerelease_tag} tag: {e}", file=sys.stderr)
        return 1


def handle_create_prod_tag(args):
    """Handle create_prod_tag command."""
    repo_path = getattr(args, 'repo_path', get_repo_path())
    vcm = VersionControlManager(repo_path)
    try:
        result = vcm.create_prod_tag(tag=args.tag)
        if args.detailed:
            print(f"Created production tag: {result}")
        else:
            print(result)
        return 0
    except ValueError as e:
        print(f"Error: Invalid tag format - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error creating production tag: {e}", file=sys.stderr)
        return 1


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Git semantic versioning operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s get-current-tag
  %(prog)s increment-prerelease --tag 1.0.0-dev.1 --prerelease-tag dev
  %(prog)s init-rc --prerelease-tag dev
  %(prog)s init-patch
  %(prog)s get-current-rc-patch --tag 1.0.0 --prerelease-tag rc
  %(prog)s increment-rc-patch --tag 1.0.0 --prerelease-tag rc
  %(prog)s create-prod --tag 1.0.0-rc.3
        """
    )
    
    parser.add_argument(
        '--repo-path',
        default=get_repo_path(),
        help='Path to the Git repository (default: current directory)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # get_current_tag command
    get_current_tag_parser = subparsers.add_parser(
        'get-current-tag',
        help='Get the current semantic version tag (dev/rc/patch/production)'
    )
    get_current_tag_parser.add_argument(
        '--repo-path',
        default=get_repo_path(),
        help='Path to the Git repository (default: current directory)'
    )
    get_current_tag_parser.add_argument(
        '--prerelease-tag',
        default='dev',
        help='Prerelease identifier (default: dev)'
    )
    get_current_tag_parser.add_argument(
        '--production',
        action='store_true',
        help='Return the latest production tag instead of prerelease'
    )
    get_current_tag_parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show descriptive message'
    )
    get_current_tag_parser.set_defaults(func=handle_get_current_tag)
    
    # increment_prerelease_tag command
    increment_parser = subparsers.add_parser(
        'increment-prerelease',
        help='Create and increment a prerelease tag'
    )
    increment_parser.add_argument(
        '--repo-path',
        default=get_repo_path(),
        help='Path to the Git repository (default: current directory)'
    )
    increment_parser.add_argument(
        '--tag',
        help='Base tag to increment from (optional, starts with 0.1.0-dev.1 if not provided)'
    )
    increment_parser.add_argument(
        '--prerelease-tag',
        default='dev',
        help='Prerelease identifier (default: dev)'
    )
    increment_parser.add_argument(
        '--major-bump',
        action='store_true',
        help='Perform major version bump instead of minor'
    )
    increment_parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show descriptive message'
    )
    increment_parser.set_defaults(func=handle_increment_prerelease)
    
    # init_new_rc command
    rc_parser = subparsers.add_parser(
        'init-rc',
        help='Initialize a new release candidate from development tag'
    )
    rc_parser.add_argument(
        '--repo-path',
        default=get_repo_path(),
        help='Path to the Git repository (default: current directory)'
    )
    rc_parser.add_argument(
        '--prerelease-tag',
        default='dev',
        help='Development prerelease identifier (default: dev)'
    )
    rc_parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show descriptive message'
    )
    rc_parser.set_defaults(func=handle_init_new_rc)
    
    # init_new_patch command
    patch_parser = subparsers.add_parser(
        'init-patch',
        help='Initialize a new patch prerelease from production tag'
    )
    patch_parser.add_argument(
        '--repo-path',
        default=get_repo_path(),
        help='Path to the Git repository (default: current directory)'
    )
    patch_parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show descriptive message'
    )
    patch_parser.set_defaults(func=handle_init_new_patch)
    
    # get_current_rc_patch command
    get_current_rc_patch_parser = subparsers.add_parser(
        'get-current-rc-patch',
        help='Get the current highest RC or patch tag for a version'
    )
    get_current_rc_patch_parser.add_argument(
        '--repo-path',
        default=get_repo_path(),
        help='Path to the Git repository (default: current directory)'
    )
    get_current_rc_patch_parser.add_argument(
        '--tag',
        help='Base production version tag (e.g., 1.0.0)'
    )
    get_current_rc_patch_parser.add_argument(
        '--prerelease-tag',
        default='rc',
        choices=['rc', 'patch'],
        help='Prerelease type (default: rc)'
    )
    get_current_rc_patch_parser.set_defaults(func=handle_get_current_rc_patch)
    
    # increment_rc_patch command
    increment_rc_patch_parser = subparsers.add_parser(
        'increment-rc-patch',
        help='Increment a release candidate or patch prerelease tag'
    )
    increment_rc_patch_parser.add_argument(
        '--repo-path',
        default=get_repo_path(),
        help='Path to the Git repository (default: current directory)'
    )
    increment_rc_patch_parser.add_argument(
        '--tag',
        help='Base production version tag (e.g., 1.0.0)'
    )
    increment_rc_patch_parser.add_argument(
        '--prerelease-tag',
        default='rc',
        choices=['rc', 'patch'],
        help='Prerelease type (default: rc)'
    )
    increment_rc_patch_parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show descriptive message'
    )
    increment_rc_patch_parser.set_defaults(func=handle_increment_rc_patch)
    
    # create_prod_tag command
    prod_parser = subparsers.add_parser(
        'create-prod',
        help='Create a production tag from RC or patch prerelease'
    )
    prod_parser.add_argument(
        '--repo-path',
        default=get_repo_path(),
        help='Path to the Git repository (default: current directory)'
    )
    prod_parser.add_argument(
        '--tag',
        help='RC or patch prerelease tag to promote (e.g., 1.0.0-rc.3)'
    )
    prod_parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show descriptive message'
    )
    prod_parser.set_defaults(func=handle_create_prod_tag)
    
    return parser


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Ensure the repo path exists
    repo_path = getattr(args, 'repo_path', get_repo_path())
    if not os.path.exists(repo_path):
        print(f"Error: Repository path '{repo_path}' does not exist", file=sys.stderr)
        return 1
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
