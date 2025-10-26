# xwords
#### nyt xword navel-gazing project

This is a project for analyzing and visualizing my New York Times
Crossword puzzle solves. Data is automatically fetched from the NYT API
using [nyt-crossword-stats](https://github.com/mattdodge/nyt-crossword-stats).

Historical data from 11 years of pen/paper NYT crossword solves
has been lost irrevocably to the sands of time.

## Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure NYT Credentials

Create a `.env` file with your NYT credentials:

```bash
cp .env.example .env
```

Then edit `.env` and add your NYT email and password:

```
NYT_EMAIL=your.email@example.com
NYT_PASSWORD=your_password_here
```

### 3. Fetch Your Data

Run the update script to fetch your crossword stats:

```bash
# Fetch last 30 days (default)
python update_data.py

# Fetch all data from a specific start date
python update_data.py --start-date 2024-01-01

# Fetch specific date range
python update_data.py --start-date 2024-01-01 --end-date 2024-12-31

# Fetch mini puzzles instead of daily
python update_data.py --type mini
```

This will create/update `xwstats.csv` with your puzzle data.

**Fields available from the NYT API:**
- Solved, Puzzle Date, Day of Week, Time Taken
- Completed At (ET), Constructor

**Fields from xwstats.com NOT available in the API:**
- Checks, Reveals, Adjusted Time, Average Time, Average Adjusted Time, Excluded

Your R code should handle the missing columns gracefully or you can update it to work with the available fields.

### 4. Run Analysis

Open `xwords.qmd` in RStudio and render to generate visualizations.

## Workflow

1. Update your data: `python update_data.py`
2. Analyze in R: Open and render `xwords.qmd` in RStudio

The fetch script outputs the same CSV format as xwstats.com, including the completion datetime (`Completed At (ET)`) field, so all your existing analyses will work without modification.
