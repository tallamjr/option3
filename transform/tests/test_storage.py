import tempfile
from pathlib import Path

import polars as pl

from transform.processor import events_to_dataframe
from transform.storage import read_all_parquet, write_batch_to_parquet

SAMPLE_EVENTS = [
    {
        "id": 2001,
        "type": "edit",
        "wiki": "enwiki",
        "title": "Test Article",
        "user": "TestUser",
        "bot": False,
        "minor": False,
        "comment": "Test edit",
        "timestamp": 1709500100,
        "server_name": "en.wikipedia.org",
        "namespace": 0,
        "length": {"old": 1000, "new": 1100},
    },
    {
        "id": 2002,
        "type": "new",
        "wiki": "wikidatawiki",
        "title": "Q999999999",
        "user": "AnotherUser",
        "bot": False,
        "minor": False,
        "comment": "Created item",
        "timestamp": 1709500200,
        "server_name": "www.wikidata.org",
        "namespace": 0,
        "length": {"old": None, "new": 300},
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
        assert loaded.height == 2
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
        assert combined.height == 4
