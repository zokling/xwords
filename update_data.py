#!/usr/bin/env python3
"""
Wrapper script to update NYT crossword stats data.
Loads credentials from .env file and fetches puzzle data.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description="Update NYT Crossword stats data (filters by COMPLETION date, only includes solved puzzles)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get puzzles completed in last 30 days (default)
  python update_data.py

  # Get all puzzles completed since a specific date
  python update_data.py --start-date 2024-01-01

  # Get puzzles completed in a specific date range
  python update_data.py --start-date 2024-01-01 --end-date 2024-12-31

  # Get mini puzzles instead of daily
  python update_data.py --type mini

  # Control publication date range (default queries 2 years back to catch late solves)
  python update_data.py --start-date 2024-01-01 --pub-start-date 2020-01-01
        """
    )

    parser.add_argument(
        "-s", "--start-date",
        help="First COMPLETION date (YYYY-MM-DD), defaults to 30 days ago",
        default=None
    )
    parser.add_argument(
        "-e", "--end-date",
        help="Last COMPLETION date (YYYY-MM-DD), defaults to today",
        default=None
    )
    parser.add_argument(
        "--pub-start-date",
        help="First PUBLICATION date to query (YYYY-MM-DD), defaults to 2 years before start-date",
        default=None
    )
    parser.add_argument(
        "--pub-end-date",
        help="Last PUBLICATION date to query (YYYY-MM-DD), defaults to today",
        default=None
    )
    parser.add_argument(
        "-t", "--type",
        help='Puzzle type: "daily", "mini", or "bonus" (default: daily)',
        default="daily",
        choices=["daily", "mini", "bonus"]
    )

    args = parser.parse_args()

    # Check for credentials in environment
    email = os.getenv("NYT_EMAIL")
    password = os.getenv("NYT_PASSWORD")
    cookie = os.getenv("NYT_COOKIE")

    if not cookie and (not email or not password):
        print("ERROR: Missing credentials!")
        print("\nPlease create a .env file with your NYT credentials.")
        print("Copy .env.example to .env and fill in your information:")
        print("  cp .env.example .env")
        print("\nThen edit .env to add your NYT email and password.")
        sys.exit(1)

    # Build command arguments
    cmd_args = [
        "python", "fetch_puzzle_stats.py",
        "-o", "xwstats.csv"
    ]

    # Add credentials
    if email and password:
        cmd_args.extend(["-u", email, "-p", password])

    # Add completion date range
    if args.start_date:
        cmd_args.extend(["-s", args.start_date])

    if args.end_date:
        cmd_args.extend(["-e", args.end_date])

    # Add publication date range
    if args.pub_start_date:
        cmd_args.extend(["--pub-start-date", args.pub_start_date])

    if args.pub_end_date:
        cmd_args.extend(["--pub-end-date", args.pub_end_date])

    # Add puzzle type
    if args.type != "daily":
        cmd_args.extend(["-t", args.type])

    print("=" * 60)
    print("NYT Crossword Stats Updater")
    print("=" * 60)
    print(f"\nFetching COMPLETED {args.type} puzzles...")
    print("\nCompletion date range:")
    if args.start_date:
        print(f"  Start: {args.start_date}")
    else:
        default_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        print(f"  Start: {default_start} (last 30 days)")

    if args.end_date:
        print(f"  End: {args.end_date}")
    else:
        print(f"  End: {datetime.now().strftime('%Y-%m-%d')} (today)")

    if args.pub_start_date or args.pub_end_date:
        print("\nPublication date range:")
        if args.pub_start_date:
            print(f"  Start: {args.pub_start_date}")
        if args.pub_end_date:
            print(f"  End: {args.pub_end_date}")

    print("\nRunning data fetch...\n")

    # Execute the fetch script
    import subprocess
    result = subprocess.run(cmd_args, capture_output=False)

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("SUCCESS! Data updated in xwstats.csv")
        print("=" * 60)
        print("\nYou can now run your R/Quarto analysis:")
        print("  Open xwords.qmd in RStudio and render")
        print("\nNote: Output columns (snake_case):")
        print("  - solved, puzzle_date, day_of_week")
        print("  - time_taken, completed_at_et, constructor")
        print("\nOnly COMPLETED puzzles are included.")
        print("Filtered by COMPLETION date, not publication date.")
    else:
        print("\n" + "=" * 60)
        print("ERROR: Data fetch failed")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
