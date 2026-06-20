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

Then load these into your Google Calendar:
* Settings menu > Settings > Import & export > Import > Select file from your computer > Import
