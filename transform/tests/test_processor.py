import polars as pl
from polars.testing import assert_frame_equal

from transform.processor import (
    activity_by_type,
    edits_by_wiki,
    events_to_dataframe,
    top_editors,
)

# Fixture data representing real Wikimedia recentchange events
RAW_EVENTS = [
    {
        "id": 1001,
        "type": "edit",
        "wiki": "enwiki",
        "title": "Albert Einstein",
        "user": "EditorAlpha",
        "bot": False,
        "minor": False,
        "comment": "Fixed citation",
        "timestamp": 1709500000,
        "server_name": "en.wikipedia.org",
        "namespace": 0,
        "length": {"old": 15000, "new": 15200},
    },
    {
        "id": 1002,
        "type": "edit",
        "wiki": "enwiki",
        "title": "Photosynthesis",
        "user": "BotGamma",
        "bot": True,
        "minor": True,
        "comment": "Fixing references",
        "timestamp": 1709500010,
        "server_name": "en.wikipedia.org",
        "namespace": 0,
        "length": {"old": 22000, "new": 22050},
    },
    {
        "id": 1003,
        "type": "new",
        "wiki": "wikidatawiki",
        "title": "Q123456789",
        "user": "EditorAlpha",
        "bot": False,
        "minor": False,
        "comment": "Created item",
        "timestamp": 1709500020,
        "server_name": "www.wikidata.org",
        "namespace": 0,
        "length": {"old": None, "new": 500},
    },
    {
        "id": 1004,
        "type": "log",
        "wiki": "enwiki",
        "title": "User:SpamAccount",
        "user": "AdminDelta",
        "bot": False,
        "minor": False,
        "comment": "Blocked for spam",
        "timestamp": 1709500030,
        "server_name": "en.wikipedia.org",
        "namespace": 2,
        "length": None,
    },
    {
        "id": 1005,
        "type": "edit",
        "wiki": "commonswiki",
        "title": "File:Sunset.jpg",
        "user": "EditorBeta",
        "bot": False,
        "minor": False,
        "comment": "Updated description",
        "timestamp": 1709500040,
        "server_name": "commons.wikimedia.org",
        "namespace": 6,
        "length": {"old": 800, "new": 950},
    },
]


def test_events_to_dataframe_columns():
    df = events_to_dataframe(RAW_EVENTS)
    assert df.height == 5
    expected_cols = {
        "id",
        "event_type",
        "wiki",
        "title",
        "user",
        "bot",
        "minor",
        "comment",
        "timestamp",
        "server_name",
        "namespace",
        "length_old",
        "length_new",
    }
    assert set(df.columns) == expected_cols


def test_events_to_dataframe_values():
    df = events_to_dataframe(RAW_EVENTS)
    titles = df["title"].to_list()
    assert "Albert Einstein" in titles
    assert "Q123456789" in titles


def test_edits_by_wiki():
    df = events_to_dataframe(RAW_EVENTS)
    result = edits_by_wiki(df)

    wikis = result["wiki"].to_list()
    assert "enwiki" in wikis
    assert "wikidatawiki" in wikis
    assert "commonswiki" in wikis
    # "log" events should be excluded
    assert result.height == 3

    enwiki_row = result.filter(pl.col("wiki") == "enwiki")
    assert enwiki_row["edit_count"].item() == 2


def test_top_editors():
    df = events_to_dataframe(RAW_EVENTS)
    result = top_editors(df, limit=10)

    # EditorAlpha has 2 edits (one edit + one new)
    top_user = result.row(0)
    assert top_user[0] == "EditorAlpha"
    assert top_user[1] == 2


def test_top_editors_limit():
    df = events_to_dataframe(RAW_EVENTS)
    result = top_editors(df, limit=2)
    assert result.height == 2


def test_activity_by_type():
    df = events_to_dataframe(RAW_EVENTS)
    result = activity_by_type(df)

    types = result["event_type"].to_list()
    assert "edit" in types
    assert "new" in types
    assert "log" in types

    edit_row = result.filter(pl.col("event_type") == "edit")
    assert edit_row["count"].item() == 3
