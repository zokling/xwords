# xwords
#### nyt xword navel-gazing project

This is a project for analyzing and visualizing my New York Times
Crossword puzzle solves. Data is automatically fetched from the NYT API
using an adapted version of [nyt-crossword-stats](https://github.com/mattdodge/nyt-crossword-stats).

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

# Fetch all data from a specific start date of puzzle completion
python update_data.py --start-date 2024-01-01

# Fetch specific date range for puzzle completion
python update_data.py --start-date 2024-01-01 --end-date 2024-12-31

# Fetch mini puzzles instead of daily
python update_data.py --type mini
```
