import re
import sys
import argparse
import urllib.request
import datetime as dt
from typing import NamedTuple
from bs4 import BeautifulSoup


RGX_SEASON = re.compile(r"Fall|Summer|Spring|Winter")
# Event: Date stuff
RGX_EVENT_DATE = re.compile(r"^(?P<event>.+): (?P<date_full>.+)$")
# month day, 202*
RGX_LONG_DATE = re.compile(r"[^\s]*?\s\d{1,2},\s202\d")
# https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
# month day, year
STRPTIME_FMT = "%B %d, %Y"

# https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform%3DDesktop#zippy=%2Ccreate-or-edit-a-csv-file
GOOGLE_CALENDAR_EVENT_HEADER = (
    "Subject",
    "Start Date",
    "Start Time",
    "End Date",
    "End Time",
    "All Day Event",
    "Description",
    "Location",
    "Private",
)


def last_day_of_month(any_day: dt.datetime) -> dt.datetime:
    """
    Get last day of the month
    * Adapted from https://stackoverflow.com/a/13565185
    """
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + dt.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - dt.timedelta(days=next_month.day)


class GoogleCalendarEvent(NamedTuple):
    """
    Google calendar event.
    """

    Subject: str
    StartDate: dt.datetime
    EndDate: dt.datetime
    StartTime: dt.datetime | None = None
    EndTime: dt.datetime | None = None
    Description: str | None = None
    Location: str | None = None
    AllDayEvent: bool = True
    Private: bool = True

    def as_csv(self) -> str:
        """
        Convert event to a CSV line.
        * Existing commas are removed
        """
        fields = []
        for col in GOOGLE_CALENDAR_EVENT_HEADER:
            # Each field is same as header but without space
            field = getattr(self, col.replace(" ", ""))
            if isinstance(field, dt.datetime):
                field_str = field.strftime("%m/%d/%y")
            elif not field:
                field_str = ""
            else:
                # Remove exiting commas
                field_str = str(field).replace(",", "")
            fields.append(field_str)
        return ",".join(fields)

    def header():
        """
        Print Google calendar event header as a CSV line.
        """
        return ",".join(GOOGLE_CALENDAR_EVENT_HEADER)


def get_adjusted_date(
    datetime: dt.datetime,
    delta_years: int = 0,
    delta_weeks: int = 0,
    delta_days: int = 0,
) -> dt.datetime:
    """
    Adjust date based on change in years, weeks, or days.
    * Uses `datetime.isocalendar`
    * Reference: https://stackoverflow.com/a/2600864
    """
    iso_year, week, day = datetime.isocalendar()
    return dt.date.fromisocalendar(
        iso_year + delta_years, week + delta_weeks, day + delta_days
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-i",
        "--url",
        help="URL to first-year schedule page for UoU",
        default="https://bioscience.utah.edu/current_students/first-year.php",
    )
    ap.add_argument(
        "-o", "--output", default=sys.stdout, help="Google calendar schedule as CSV"
    )
    ap.add_argument(
        "-y",
        "--delta_years",
        default=0,
        type=int,
        help="Add this number of years to the dates from the URL.",
    )
    ap.add_argument(
        "-w",
        "--delta_weeks",
        default=0,
        type=int,
        help="Add this number of weeks to the dates from the URL.",
    )
    ap.add_argument(
        "-d",
        "--delta_days",
        default=0,
        type=int,
        help="Add this number of days to the dates from the URL.",
    )
    args = ap.parse_args()
    with urllib.request.urlopen(args.url) as fp:
        contents = fp.read().decode("utf8")

    html = BeautifulSoup(contents, features="html.parser")
    # Print header
    print(GoogleCalendarEvent.header())

    for tag in html.find_all("h3", string=RGX_SEASON):
        mtch_year = re.search(r"202\d", tag.string)
        if not mtch_year:
            continue
        year = int(mtch_year.group()) + args.delta_years
        print(f"On {tag.string}. Adjusted year: {year}", file=sys.stderr)

        # Is contained in a div
        for child_tag in tag.parent.contents:
            if child_tag.name == "h3":
                continue
            child_tag_str = child_tag.get_text()
            if not child_tag_str:
                continue
            mtch = RGX_EVENT_DATE.search(child_tag_str)
            if not mtch:
                continue
            mtch_grps = mtch.groupdict()
            if not mtch_grps:
                continue

            event = mtch_grps["event"]
            # Label first and second half with year.
            # "1st Half" -> "Spring 2025 Classes - 1st Half"
            if event == "1st Half" or event == "2nd Half":
                event = f"{tag.string} - {event}"

            date = mtch_grps["date_full"]
            mtch_date_elems: list[re.Match] = RGX_LONG_DATE.findall(date)
            if mtch_date_elems:
                # Adjust date based on ISO date
                # https://en.wikipedia.org/wiki/ISO_week_date
                # https://stackoverflow.com/a/2600864
                start_date = dt.datetime.strptime(mtch_date_elems[0], STRPTIME_FMT)
                start_date = get_adjusted_date(
                    start_date,
                    delta_years=args.delta_years,
                    delta_weeks=args.delta_weeks,
                    delta_days=args.delta_days,
                )
                try:
                    end_date = dt.datetime.strptime(mtch_date_elems[1], STRPTIME_FMT)
                    end_date = get_adjusted_date(
                        end_date,
                        delta_years=args.delta_years,
                        delta_weeks=args.delta_weeks,
                        delta_days=args.delta_days,
                    )
                except IndexError:
                    end_date = start_date

                gc_event = GoogleCalendarEvent(
                    Subject=event,
                    StartDate=start_date,
                    EndDate=end_date,
                )
                print(gc_event.as_csv())
            else:
                # Assume month and pass to datetime to check
                date_month = dt.datetime.strptime(date, "%B")
                start_date = date_month.replace(day=1, year=year)
                end_date = last_day_of_month(date_month).replace(year=year)
                gc_event = GoogleCalendarEvent(
                    Subject=event,
                    StartDate=start_date,
                    EndDate=end_date,
                )
                print(gc_event.as_csv())


if __name__ == "__main__":
    raise SystemExit(main())
