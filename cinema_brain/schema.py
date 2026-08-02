SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_files (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    headers_json TEXT NOT NULL,
    classified_as TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS films (
    film_key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    year INTEGER,
    letterboxd_uri TEXT,
    watched INTEGER NOT NULL DEFAULT 0,
    rating REAL,
    liked INTEGER NOT NULL DEFAULT 0,
    watchlist INTEGER NOT NULL DEFAULT 0,
    first_watched_date TEXT,
    last_watched_date TEXT,
    watch_count INTEGER NOT NULL DEFAULT 0,
    review_count INTEGER NOT NULL DEFAULT 0,
    list_count INTEGER NOT NULL DEFAULT 0,
    evidence_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS viewing_events (
    id INTEGER PRIMARY KEY,
    film_key TEXT NOT NULL REFERENCES films(film_key),
    watched_date TEXT,
    rewatch INTEGER NOT NULL DEFAULT 0,
    rating REAL,
    tags TEXT,
    source_path TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    UNIQUE(source_path, source_row)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    film_key TEXT NOT NULL REFERENCES films(film_key),
    review_date TEXT,
    rating REAL,
    rewatch INTEGER NOT NULL DEFAULT 0,
    review_text TEXT,
    tags TEXT,
    source_path TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    UNIQUE(source_path, source_row)
);

CREATE TABLE IF NOT EXISTS list_entries (
    id INTEGER PRIMARY KEY,
    film_key TEXT NOT NULL REFERENCES films(film_key),
    list_name TEXT NOT NULL,
    rank_value INTEGER,
    notes TEXT,
    source_path TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    UNIQUE(source_path, source_row)
);

CREATE INDEX IF NOT EXISTS idx_films_watched ON films(watched);
CREATE INDEX IF NOT EXISTS idx_films_watchlist ON films(watchlist);
CREATE INDEX IF NOT EXISTS idx_films_rating ON films(rating);
CREATE INDEX IF NOT EXISTS idx_events_film ON viewing_events(film_key);
"""
