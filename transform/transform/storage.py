from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import structlog

logger = structlog.get_logger()


def write_batch_to_parquet(df: pl.DataFrame, output_dir: str) -> Path:
    """Write a DataFrame batch to a timestamped parquet file."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = out / f"events_{ts}.parquet"
    df.write_parquet(path)
    logger.info("parquet_written", path=str(path), rows=df.height)
    return path


def read_all_parquet(parquet_dir: str) -> pl.DataFrame:
    """Lazily scan all parquet files in a directory and collect."""
    pattern = f"{parquet_dir}/*.parquet"
    return pl.scan_parquet(pattern).collect()
