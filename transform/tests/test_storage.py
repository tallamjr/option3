import tempfile
from pathlib import Path

import polars as pl

from transform.processor import events_to_dataframe
from transform.storage import read_all_parquet, write_batch_to_parquet

# Real events captured from the live Wikimedia EventStreams SSE endpoint
# https://stream.wikimedia.org/v2/stream/recentchange on 2026-03-04
SAMPLE_EVENTS = [
    {
        "id": 2002470984,
        "type": "edit",
        "wiki": "enwiki",
        "title": "March 7",
        "user": "PontiffSulivahn",
        "bot": False,
        "minor": False,
        "comment": "Added entries + added references",
        "timestamp": 1772660481,
        "server_name": "en.wikipedia.org",
        "namespace": 0,
        "length": {"old": 80518, "new": 81143},
    },
    {
        "id": 2545870133,
        "type": "edit",
        "wiki": "wikidatawiki",
        "title": "Q20060181",
        "user": "KrBot",
        "bot": True,
        "minor": False,
        "comment": "/* wbsetreference-set:2| */ [[Property:P685]]: 878061",
        "timestamp": 1772660485,
        "server_name": "www.wikidata.org",
        "namespace": 0,
        "length": {"old": 25171, "new": 25171},
    },
    {
        "id": 3221685413,
        "type": "new",
        "wiki": "commonswiki",
        "title": "Category:October 2009 at Sheremetyevo International Airport",
        "user": "Ardfern",
        "bot": False,
        "minor": False,
        "comment": "cat added",
        "timestamp": 1772660485,
        "server_name": "commons.wikimedia.org",
        "namespace": 14,
        "length": {"old": None, "new": 142},
    },
]


def test_write_batch_creates_parquet_file():
    df = events_to_dataframe(SAMPLE_EVENTS)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_batch_to_parquet(df, tmpdir)
        assert path.exists()
        assert path.suffix == ".parquet"
        assert path.stat().st_size > 0


def test_write_batch_contents_roundtrip():
    df = events_to_dataframe(SAMPLE_EVENTS)
    with tempfile.TemporaryDirectory() as tmpdir:
        write_batch_to_parquet(df, tmpdir)
        loaded = read_all_parquet(tmpdir)
        assert loaded.height == 3
        assert set(loaded.columns) == set(df.columns)


def test_write_creates_output_directory():
    df = events_to_dataframe(SAMPLE_EVENTS)
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = str(Path(tmpdir) / "sub" / "dir")
        path = write_batch_to_parquet(df, nested)
        assert path.exists()


def test_read_all_parquet_multiple_files():
    df = events_to_dataframe(SAMPLE_EVENTS)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the same batch twice to create two parquet files
        write_batch_to_parquet(df, tmpdir)
        # Ensure second file gets different timestamp
        import time

        time.sleep(1.1)
        write_batch_to_parquet(df, tmpdir)

        combined = read_all_parquet(tmpdir)
        assert combined.height == 6
