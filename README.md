# Cinema Brain

A private, local-first recommendation engine for Daniel's Letterboxd history.

## What it does

- Ingests Letterboxd CSV exports.
- Normalizes films across watched, ratings, diary, watchlist, reviews, likes, and lists.
- Preserves every viewing event and rewatch.
- Validates duplicates, conflicting records, malformed dates, and missing identifiers.
- Builds a SQLite database for deterministic watched-film exclusion.
- Generates a baseline taste report.
- Provides a command-line recommendation shortlist from the existing watchlist.

## Privacy

Raw Letterboxd exports remain local and are ignored by Git by default. Do not commit
private exports unless you intentionally want them stored in the repository.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy the unzipped Letterboxd CSV files into data/raw/
python -m cinema_brain ingest
python -m cinema_brain validate
python -m cinema_brain report
python -m cinema_brain recommend --genre "romance" --limit 10
```

## Expected exports

The loader discovers CSVs recursively and recognizes common Letterboxd exports:
`watched.csv`, `ratings.csv`, `diary.csv`, `watchlist.csv`, `reviews.csv`,
`profile.csv`, and liked-film/list/review exports.

Because Letterboxd may place multiple files with the same filename in different
folders, classification also uses headers and parent-folder names.

## Definition of done

Cinema Brain is established when:

1. Every source CSV has a recorded row count and checksum.
2. Every film-like row is normalized to a stable key.
3. Every diary viewing is retained.
4. Watched exclusions are deterministic.
5. Validation passes with no unexplained critical errors.
6. Recommendations cite the evidence used.
