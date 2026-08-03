import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from cinema_brain.schema import SCHEMA_SQL


def test_personal_taste_graph_cli_writes_output(tmp_path: Path):
    db = tmp_path / "cinema.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT INTO films (film_key,name,year,watched,rating,liked,watch_count) VALUES(?,?,?,?,?,?,?)",
        ("title:undertone:2025", "Undertone", 2025, 1, 4.5, 1, 2),
    )
    conn.commit()
    conn.close()

    profiles = tmp_path / "profiles.json"
    profiles.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "registry_version": "1.0.0",
                "films": [
                    {
                        "film_key": "title:undertone:2025",
                        "title": "Undertone",
                        "year": 2025,
                        "status": "reviewed",
                        "traits": [
                            {"trait_id": "creeping_dread", "value": 0.98, "confidence": 0.99}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "graph.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cinema_brain.cli",
            "--db",
            str(db),
            "personal-taste-graph",
            "--profiles",
            str(profiles),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.exists()
    graph = json.loads(output.read_text(encoding="utf-8"))
    assert graph["traits"]["creeping_dread"]["affinity"] > 0
