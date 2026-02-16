"""CLI tool to adjust daily token cap.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.

Admin CLI for adjusting the daily token cap without redeployment (REQ-8).

Usage:
    poetry run python tools/admin_token_cap.py set --cap 30 --admin-id admin@example.com
    poetry run python tools/admin_token_cap.py get
    poetry run python tools/admin_token_cap.py status
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

# Add src to path so we can import auth modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from auth.token_cap_service import (
    get_current_cap,
    get_today_key,
    set_daily_cap,
    CAP_CONFIG_PK,
    COUNTER_SK_PREFIX,
    _get_dynamodb_resource,
)

logger = logging.getLogger(__name__)

TOKEN_CAP_TABLE = os.environ.get("TOKEN_CAP_TABLE", "aletheia-token-cap")


def cmd_set(args: argparse.Namespace) -> int:
    """Set the daily token cap to a new value.

    Args:
        args: Parsed CLI arguments with cap and admin_id.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    new_cap = args.cap
    admin_id = args.admin_id
    table_name = args.table or TOKEN_CAP_TABLE

    if new_cap <= 0:
        print(f"Error: Cap must be a positive integer, got {new_cap}")
        return 1

    try:
        success = set_daily_cap(table_name, new_cap, admin_id)
        if success:
            print(f"Daily cap updated to {new_cap} by {admin_id}")
            logger.info(
                "Admin cap change: new_cap=%d, admin_id=%s, table=%s",
                new_cap,
                admin_id,
                table_name,
            )
            return 0
        else:
            print("Error: Failed to update daily cap")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        logger.error("Failed to set daily cap: %s", e)
        return 1


def cmd_get(args: argparse.Namespace) -> int:
    """Get the current daily token cap.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    table_name = args.table or TOKEN_CAP_TABLE

    try:
        current_cap = get_current_cap(table_name)
        print(f"Current daily cap: {current_cap}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        logger.error("Failed to get daily cap: %s", e)
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show current cap status including today's usage.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    table_name = args.table or TOKEN_CAP_TABLE

    try:
        current_cap = get_current_cap(table_name)
        today_key = get_today_key()
        counter_sk = f"{COUNTER_SK_PREFIX}{today_key}"

        # Read today's count directly from DynamoDB
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(table_name)

        try:
            response = table.get_item(
                Key={"PK": CAP_CONFIG_PK, "SK": counter_sk},
            )
            item = response.get("Item", {})
            current_count = int(item.get("tokens_issued", 0))
        except Exception:
            current_count = 0

        remaining = max(0, current_cap - current_count)

        print(f"Date (UTC):     {today_key}")
        print(f"Daily cap:      {current_cap}")
        print(f"Tokens issued:  {current_count}")
        print(f"Remaining:      {remaining}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        logger.error("Failed to get status: %s", e)
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the admin token cap CLI.

    Returns:
        Configured argparse.ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        description="Admin CLI tool to manage daily token cap (Issue #341)",
    )
    parser.add_argument(
        "--table",
        default=None,
        help=f"DynamoDB table name (default: {TOKEN_CAP_TABLE})",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # set command
    set_parser = subparsers.add_parser("set", help="Set the daily token cap")
    set_parser.add_argument(
        "--cap",
        type=int,
        required=True,
        help="New daily cap value (positive integer)",
    )
    set_parser.add_argument(
        "--admin-id",
        required=True,
        help="Admin identifier for audit trail",
    )

    # get command
    subparsers.add_parser("get", help="Get the current daily cap")

    # status command
    subparsers.add_parser("status", help="Show current cap status and usage")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the admin token cap CLI.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "set": cmd_set,
        "get": cmd_get,
        "status": cmd_status,
    }

    handler = commands.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
