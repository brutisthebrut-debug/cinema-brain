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

CREATE TABLE IF NOT EXISTS rss_items (
    guid TEXT PRIMARY KEY,
    feed_url TEXT NOT NULL,
    link TEXT NOT NULL,
    title TEXT NOT NULL,
    film_title TEXT,
    film_year INTEGER,
    watched_date TEXT,
    member_rating REAL CHECK(member_rating IS NULL OR (member_rating >= 0 AND member_rating <= 5)),
    rewatch INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    item_type TEXT NOT NULL CHECK(item_type IN ('diary', 'review', 'list')),
    content_hash TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS film_metadata (
    film_key TEXT NOT NULL REFERENCES films(film_key) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    title TEXT NOT NULL,
    year INTEGER,
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    runtime_minutes INTEGER CHECK(runtime_minutes IS NULL OR runtime_minutes > 0),
    genres_json TEXT NOT NULL DEFAULT '[]',
    directors_json TEXT NOT NULL DEFAULT '[]',
    cast_json TEXT NOT NULL DEFAULT '[]',
    countries_json TEXT NOT NULL DEFAULT '[]',
    languages_json TEXT NOT NULL DEFAULT '[]',
    keywords_json TEXT NOT NULL DEFAULT '[]',
    retrieved_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY(film_key, provider)
);

CREATE TABLE IF NOT EXISTS trait_evidence (
    id INTEGER PRIMARY KEY,
    film_key TEXT NOT NULL REFERENCES films(film_key),
    trait_id TEXT NOT NULL,
    polarity REAL NOT NULL CHECK(polarity >= -1 AND polarity <= 1),
    strength REAL NOT NULL CHECK(strength >= 0),
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    evidence_text TEXT,
    model_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(film_key, trait_id, source_type, source_ref, model_version)
);

CREATE TABLE IF NOT EXISTS recommendation_runs (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    request_json TEXT NOT NULL,
    model_version TEXT NOT NULL,
    candidate_count INTEGER NOT NULL,
    selected_film_key TEXT REFERENCES films(film_key),
    predicted_score REAL,
    confidence REAL,
    explanation_json TEXT NOT NULL,
    availability_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recommendation_candidates (
    run_id TEXT NOT NULL REFERENCES recommendation_runs(id) ON DELETE CASCADE,
    film_key TEXT NOT NULL REFERENCES films(film_key),
    rank_position INTEGER NOT NULL,
    score REAL NOT NULL,
    accepted INTEGER NOT NULL DEFAULT 0,
    rejection_reasons_json TEXT NOT NULL DEFAULT '[]',
    score_components_json TEXT NOT NULL,
    PRIMARY KEY(run_id, film_key)
);

CREATE TABLE IF NOT EXISTS recommendation_outcomes (
    run_id TEXT PRIMARY KEY REFERENCES recommendation_runs(id) ON DELETE CASCADE,
    film_key TEXT NOT NULL REFERENCES films(film_key),
    started INTEGER,
    completed INTEGER,
    actual_rating REAL CHECK(actual_rating IS NULL OR (actual_rating >= 0 AND actual_rating <= 5)),
    scared INTEGER,
    moved INTEGER,
    comforted INTEGER,
    bored INTEGER,
    surprised INTEGER,
    reaction_text TEXT,
    recorded_at TEXT NOT NULL,
    prediction_error REAL
);

CREATE INDEX IF NOT EXISTS idx_films_watched ON films(watched);
CREATE INDEX IF NOT EXISTS idx_films_watchlist ON films(watchlist);
CREATE INDEX IF NOT EXISTS idx_films_rating ON films(rating);
CREATE INDEX IF NOT EXISTS idx_events_film ON viewing_events(film_key);
CREATE INDEX IF NOT EXISTS idx_rss_published ON rss_items(published_at);
CREATE INDEX IF NOT EXISTS idx_rss_film ON rss_items(film_title, film_year);
CREATE INDEX IF NOT EXISTS idx_metadata_provider ON film_metadata(provider);
CREATE INDEX IF NOT EXISTS idx_metadata_retrieved ON film_metadata(retrieved_at);
CREATE INDEX IF NOT EXISTS idx_trait_evidence_trait ON trait_evidence(trait_id);
CREATE INDEX IF NOT EXISTS idx_trait_evidence_film ON trait_evidence(film_key);
CREATE INDEX IF NOT EXISTS idx_recommendation_runs_created ON recommendation_runs(created_at);
"""
