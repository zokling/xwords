import argparse
import os
from csv import DictWriter
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

API_ROOT = "http://www.nytimes.com/svc/crosswords"
PUZZLE_INFO = API_ROOT + "/v3/puzzles.json"
PUZZLE_DETAIL = API_ROOT + "/v6/game/"

DATE_FORMAT = "%Y-%m-%d"

parser = argparse.ArgumentParser(description="Fetch NYT Crossword stats")
parser.add_argument("-u", "--username", help="NYT Account Email Address")
parser.add_argument("-p", "--password", help="NYT Account Password")
parser.add_argument(
    "-s",
    "--start-date",
    help="The first COMPLETION date to pull from, inclusive (defaults to 30 days ago)",
    default=datetime.strftime(datetime.now() - timedelta(days=30), DATE_FORMAT),
)
parser.add_argument(
    "-e",
    "--end-date",
    help="The last COMPLETION date to pull from, inclusive (defaults to today)",
    default=datetime.strftime(datetime.now(), DATE_FORMAT),
)
parser.add_argument(
    "--pub-start-date",
    help="The first PUBLICATION date to query (defaults to 2 years before start-date to capture late solves)",
    default=None,
)
parser.add_argument(
    "--pub-end-date",
    help="The last PUBLICATION date to query (defaults to today)",
    default=None,
)
parser.add_argument(
    "-o", "--output-csv", help="The CSV file to write to", default="data.csv"
)
parser.add_argument(
    "-t",
    "--type",
    help='The type of puzzle data to fetch. Valid values are "daily", "bonus", and "mini" (defaults to daily)',
    default="daily",
)


def login(username, password):
    """Return the NYT-S cookie after logging in"""
    login_resp = requests.post(
        "https://myaccount.nytimes.com/svc/ios/v2/login",
        data={
            "login": username,
            "password": password,
        },
        headers={
            "User-Agent": "Crosswords/20191213190708 CFNetwork/1128.0.1 Darwin/19.6.0",
            "client_id": "ios.crosswords",
        },
    )
    login_resp.raise_for_status()
    for cookie in login_resp.json()["data"]["cookies"]:
        if cookie["name"] == "NYT-S":
            return cookie["cipheredValue"]
    raise ValueError("NYT-S cookie not found")


def get_v3_puzzle_overview(puzzle_type, start_date, end_date, cookie):
    payload = {
        "publish_type": puzzle_type,
        "sort_order": "asc",
        "sort_by": "print_date",
        "date_start": start_date.strftime("%Y-%m-%d"),
        "date_end": end_date.strftime("%Y-%m-%d"),
    }

    overview_resp = requests.get(PUZZLE_INFO, params=payload, cookies={"NYT-S": cookie})

    overview_resp.raise_for_status()
    puzzle_info = overview_resp.json().get("results")
    return puzzle_info


def get_v3_puzzle_detail(puzzle_id, cookie):
    puzzle_resp = requests.get(
        f"{PUZZLE_DETAIL}/{puzzle_id}.json", cookies={"NYT-S": cookie}
    )

    puzzle_resp.raise_for_status()
    puzzle_data = puzzle_resp.json()
    puzzle_detail = puzzle_data["calcs"]
    # Also get the full puzzle data to access firstSolved
    puzzle_detail["firstSolved"] = puzzle_data.get("firsts", {}).get("solved")

    return puzzle_detail


if __name__ == "__main__":
    args = parser.parse_args()
    cookie = os.getenv("NYT_COOKIE")
    if not cookie:
        cookie = login(args.username, args.password)

    # Completion date range (what we filter on)
    completion_start = datetime.strptime(args.start_date, DATE_FORMAT)
    completion_end = datetime.strptime(args.end_date, DATE_FORMAT)

    # Publication date range (what we query from API)
    # Default: query 2 years before completion start to catch late solves
    if args.pub_start_date:
        pub_start = datetime.strptime(args.pub_start_date, DATE_FORMAT)
    else:
        pub_start = completion_start - timedelta(days=730)  # 2 years buffer

    if args.pub_end_date:
        pub_end = datetime.strptime(args.pub_end_date, DATE_FORMAT)
    else:
        pub_end = datetime.now()

    days_between = (pub_end - pub_start).days
    batches = (days_between // 100) + 1

    print(
        f"Querying puzzles published {pub_start.strftime(DATE_FORMAT)} to {pub_end.strftime(DATE_FORMAT)} in {batches} batches"
    )
    print(
        f"Filtering for puzzles completed {args.start_date} to {args.end_date}"
    )

    if pub_end - pub_start > timedelta(days=100):
        batch_end = pub_start + timedelta(days=100)
    else:
        batch_end = pub_end
    batch_start = pub_start

    puzzle_overview = []

    for batch in (pbar := tqdm(range(batches))):
        pbar.set_description(f"Start date: {batch_start}")
        batch_overview = get_v3_puzzle_overview(
            puzzle_type=args.type,
            start_date=batch_start,
            end_date=batch_end,
            cookie=cookie,
        )
        puzzle_overview.extend(batch_overview)
        batch_start = batch_start + timedelta(days=100)
        batch_end = batch_end + timedelta(days=100)

    print("\nGetting puzzle solve times and filtering by completion date\n")

    filtered_puzzles = []
    for puzzle in tqdm(puzzle_overview):
        # Skip unsolved puzzles
        if not puzzle.get("solved"):
            continue

        detail = get_v3_puzzle_detail(puzzle_id=puzzle["puzzle_id"], cookie=cookie)
        puzzle["solving_seconds"] = detail.get("secondsSpentSolving", None)
        puzzle["firstSolved"] = detail.get("firstSolved", None)

        # Filter by completion date
        if puzzle["firstSolved"]:
            # Parse completion timestamp (Unix timestamp in seconds)
            completed_at = datetime.fromtimestamp(puzzle["firstSolved"])
            # Convert to date only for comparison
            completed_date = completed_at.date()

            if completed_date < completion_start.date() or completed_date > completion_end.date():
                continue
        else:
            # Skip puzzles without completion timestamp
            continue

        # Get the full day of week name (Monday, Tuesday, etc.)
        puzzle_date_obj = datetime.strptime(puzzle["print_date"], DATE_FORMAT)
        puzzle["day_of_week"] = puzzle_date_obj.strftime('%A')

        filtered_puzzles.append(puzzle)

    # Map API fields with snake_case column names
    mapped_data = []
    for puzzle in filtered_puzzles:
        mapped_puzzle = {
            "solved": puzzle.get("solved"),
            "puzzle_date": puzzle.get("print_date"),
            "day_of_week": puzzle.get("day_of_week"),
            "time_taken": puzzle.get("solving_seconds"),
            "completed_at_et": puzzle.get("firstSolved"),
            "constructor": puzzle.get("author"),
        }
        mapped_data.append(mapped_puzzle)

    fields = [
        "solved",
        "puzzle_date",
        "day_of_week",
        "time_taken",
        "completed_at_et",
        "constructor",
    ]

    print("Writing stats to {}".format(args.output_csv))

    with open(args.output_csv, "w") as f:
        writer = DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(mapped_data)

    print("{} completed puzzles written to {}".format(len(filtered_puzzles), args.output_csv))
