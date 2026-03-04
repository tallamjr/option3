import polars as pl
from polars.testing import assert_frame_equal

from transform.processor import (
    activity_by_type,
    edits_by_wiki,
    events_to_dataframe,
    top_editors,
)

# Real events captured from the live Wikimedia EventStreams SSE endpoint
# https://stream.wikimedia.org/v2/stream/recentchange on 2026-03-04
RAW_EVENTS = [
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
        "id": 2545870135,
        "type": "edit",
        "wiki": "wikidatawiki",
        "title": "Q138569005",
        "user": "Xezbeth",
        "bot": False,
        "minor": False,
        "comment": "/* wbcreateclaim-create:1| */ [[Property:P13195]]: 43601",
        "timestamp": 1772660485,
        "server_name": "www.wikidata.org",
        "namespace": 0,
        "length": {"old": 9903, "new": 10252},
    },
    {
        "id": 3221685411,
        "type": "edit",
        "wiki": "commonswiki",
        "title": "Category:Logos of companies of Venezuela",
        "user": "Rathfelder",
        "bot": False,
        "minor": True,
        "comment": "removed [[Category:Logos of Venezuela]]; added [[Category:Logos of organizations of Venezuela]]",
        "timestamp": 1772660484,
        "server_name": "commons.wikimedia.org",
        "namespace": 14,
        "length": {"old": 203, "new": 220},
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
    {
        "id": 3221685415,
        "type": "categorize",
        "wiki": "commonswiki",
        "title": "Category:WikiPortraits photographers",
        "user": "Jenny8lee",
        "bot": False,
        "comment": "[[:User:K6ka]] added to category",
        "timestamp": 1772660484,
        "server_name": "commons.wikimedia.org",
        "namespace": 14,
    },
    {
        "type": "log",
        "wiki": "enwiki",
        "title": "Teacher Retirement System of Texas",
        "user": "Rob.maxwell4655",
        "bot": False,
        "comment": "",
        "timestamp": 1772660531,
        "server_name": "en.wikipedia.org",
        "namespace": 0,
        "log_id": 0,
        "log_type": "abusefilter",
        "log_action": "hit",
    },
]


def test_events_to_dataframe_columns():
    df = events_to_dataframe(RAW_EVENTS)
    assert df.height == 7
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
    assert "March 7" in titles
    assert "Q138569005" in titles
    assert "Category:WikiPortraits photographers" in titles


def test_edits_by_wiki():
    df = events_to_dataframe(RAW_EVENTS)
    result = edits_by_wiki(df)

    wikis = result["wiki"].to_list()
    assert "enwiki" in wikis
    assert "wikidatawiki" in wikis
    assert "commonswiki" in wikis
    # Only edit+new types included; categorize and log excluded
    assert result.height == 3

    # enwiki has 1 edit (PontiffSulivahn)
    enwiki_row = result.filter(pl.col("wiki") == "enwiki")
    assert enwiki_row["edit_count"].item() == 1

    # wikidatawiki has 2 edits (KrBot, Xezbeth)
    wikidata_row = result.filter(pl.col("wiki") == "wikidatawiki")
    assert wikidata_row["edit_count"].item() == 2

    # commonswiki has 2 events (Rathfelder edit + Ardfern new)
    commons_row = result.filter(pl.col("wiki") == "commonswiki")
    assert commons_row["edit_count"].item() == 2


def test_top_editors():
    df = events_to_dataframe(RAW_EVENTS)
    result = top_editors(df, limit=10)

    # 5 distinct editors across edit+new events
    assert result.height == 5
    users = result["user"].to_list()
    assert "KrBot" in users
    assert "PontiffSulivahn" in users
    assert "Ardfern" in users

    # KrBot should be flagged as a bot
    krbot_row = result.filter(pl.col("user") == "KrBot")
    assert krbot_row["is_bot"].item() is True


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
    assert "categorize" in types
    assert "log" in types

    edit_row = result.filter(pl.col("event_type") == "edit")
    assert edit_row["count"].item() == 4

    log_row = result.filter(pl.col("event_type") == "log")
    assert log_row["count"].item() == 1
