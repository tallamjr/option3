import polars as pl


def events_to_dataframe(events: list[dict]) -> pl.DataFrame:
    """Convert a list of raw event dicts into a typed Polars DataFrame."""
    rows = []
    for e in events:
        length = e.get("length") or {}
        rows.append(
            {
                "id": e.get("id"),
                "event_type": e.get("type"),
                "wiki": e.get("wiki"),
                "title": e.get("title"),
                "user": e.get("user"),
                "bot": e.get("bot", False),
                "minor": e.get("minor", False),
                "comment": e.get("comment"),
                "timestamp": e.get("timestamp"),
                "server_name": e.get("server_name"),
                "namespace": e.get("namespace"),
                "length_old": length.get("old"),
                "length_new": length.get("new"),
            }
        )

    return pl.DataFrame(rows)


def edits_by_wiki(df: pl.DataFrame) -> pl.DataFrame:
    """Group edits by wiki: count edits and sum size changes."""
    size_change = (
        pl.col("length_new").cast(pl.Int64) - pl.col("length_old").cast(pl.Int64)
    )

    return (
        df.lazy()
        .filter(pl.col("event_type").is_in(["edit", "new"]))
        .with_columns(size_change.alias("size_change"))
        .group_by("wiki")
        .agg(
            pl.len().alias("edit_count"),
            pl.col("size_change").sum().alias("total_size_change"),
        )
        .sort("edit_count", descending=True)
        .collect()
    )


def top_editors(df: pl.DataFrame, limit: int = 20) -> pl.DataFrame:
    """Rank editors by edit count."""
    return (
        df.lazy()
        .filter(pl.col("event_type").is_in(["edit", "new"]))
        .group_by("user")
        .agg(
            pl.len().alias("edit_count"),
            pl.col("bot").first().alias("is_bot"),
        )
        .sort("edit_count", descending=True)
        .head(limit)
        .collect()
    )


def activity_by_type(df: pl.DataFrame) -> pl.DataFrame:
    """Count events grouped by event type."""
    return (
        df.lazy()
        .group_by("event_type")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .collect()
    )
