# UoU BioScience Google Calendar Creator
Creates Google Calendar events for University of Utah's 1st year BioScience program.

## Getting Started
Testing on `python==3.12.0`.
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
Get events from https://bioscience.utah.edu/current_students/first-year.php.
```bash
python main.py > uou_biosci_calendar.csv
```

Add 1 year to above link.
```bash
python main.py -y 1 > uou_biosci_calendar_plusoneyear.csv
```

Add 1 year and 1 week (**For 2026**) to above link.
```bash
python main.py -y 1 -w 1 > uou_biosci_calendar_2026.csv
```

Then load these into your Google Calendar:
* Settings menu > Settings > Import & export > Import > Select file from your computer > Import
