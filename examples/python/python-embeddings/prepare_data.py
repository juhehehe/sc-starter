# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Fetch the data of this example once: written questions to eight ministries.

Usage: uv run prepare_data.py
Writes data/questions.csv.gz: 1,000 questions per ministry, asked in the
House of Commons in 2025 and answered. You do not need to run this; the
file is in the repository. It shows where the data comes from. The API is
slow: this took 19 minutes.

The questions come from the Written Questions API of the UK Parliament,
under the Open Parliament Licence v3.0. The names of the MPs are left out:
the licence does not cover personal data, and the example does not need
them. Only the standard library, so that `uv run` installs nothing.
"""

import calendar
import csv
import gzip
import json
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://questions-statements-api.parliament.uk/api/writtenquestions/questions"
OUT = Path("data/questions.csv.gz")
YEAR = 2025
PER_MINISTRY = 1000
# Fetched month by month, so that the sample spreads over the whole year.
PER_MONTH = 150

# Short name, the ID of the ministry in the API, and whom a question to it
# addresses. Every question begins "To ask <addressee>, ...", which names
# the ministry; that beginning is cut off, or grouping would be trivial.
MINISTRIES = [
    ("Health", 17, "the Secretary of State for Health and Social Care"),
    ("Education", 60, "the Secretary of State for Education"),
    ("Home Office", 1, "the Secretary of State for the Home Department"),
    ("Defence", 11, "the Secretary of State for Defence"),
    ("Treasury", 14, "the Chancellor of the Exchequer"),
    (
        "Foreign Office",
        208,
        "the Secretary of State for Foreign, Commonwealth and Development Affairs",
    ),
    (
        "Environment",
        13,
        "the Secretary of State for Environment, Food and Rural Affairs",
    ),
    ("Transport", 27, "the Secretary of State for Transport"),
]


def fetch_month(ministry_id, month):
    """Return up to PER_MONTH answered questions to one ministry in one month."""
    last_day = calendar.monthrange(YEAR, month)[1]
    query = urllib.parse.urlencode(
        {
            "house": "Commons",
            "answered": "Answered",
            "answeringBodies": ministry_id,
            "tabledWhenFrom": f"{YEAR}-{month:02d}-01",
            "tabledWhenTo": f"{YEAR}-{month:02d}-{last_day}",
            "take": PER_MONTH,
        }
    )
    with urllib.request.urlopen(f"{API}?{query}", timeout=60) as response:
        return [item["value"] for item in json.load(response)["results"]]


def strip_addressee(text, addressee):
    """Return the question without "To ask <addressee>,", or None."""
    beginning = re.match(
        r"to ask " + re.escape(addressee) + r",?\s+", text, flags=re.IGNORECASE
    )
    return text[beginning.end() :].strip() if beginning else None


def fetch_ministry(name, ministry_id, addressee, seen):
    """Return PER_MINISTRY questions to one ministry, drawn at random.

    `seen` holds the question texts of all ministries so far: MPs sometimes
    ask the same question twice, and a text should appear only once.
    """
    rows, odd = [], 0
    for month in range(1, 13):
        for question in fetch_month(ministry_id, month):
            text = strip_addressee(question["questionText"], addressee)
            if text is None:
                odd += 1
                continue
            if text in seen:
                continue
            seen.add(text)
            rows.append(
                {
                    "id": question["id"],
                    "uin": question["uin"],
                    "date": question["dateTabled"][:10],
                    "ministry": name,
                    "heading": question["heading"].strip(),
                    "question": text,
                }
            )
        # Be gentle with the API.
        time.sleep(0.5)
    print(
        f"{name}: {len(rows)} questions, {odd} with another beginning left out",
        flush=True,
    )
    if len(rows) < PER_MINISTRY:
        raise SystemExit(f"Too few questions for {name}.")
    return random.Random(YEAR).sample(rows, PER_MINISTRY)


def main():
    """Fetch the questions of all ministries and write them to OUT."""
    # The questions of all ministries, in the order they were asked.
    seen = set()
    rows = []
    for name, ministry_id, addressee in MINISTRIES:
        rows.extend(fetch_ministry(name, ministry_id, addressee, seen))
    rows.sort(key=lambda row: (row["date"], row["id"]))

    OUT.parent.mkdir(exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} questions to {OUT}")


if __name__ == "__main__":
    main()
