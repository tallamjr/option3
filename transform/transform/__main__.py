import time

import click
import structlog

from transform.consumer import KafkaConsumer
from transform.processor import events_to_dataframe
from transform.storage import write_batch_to_parquet

logger = structlog.get_logger()


@click.command()
@click.option("--brokers", default="localhost:19092", help="Kafka broker addresses")
@click.option("--topic", default="wiki.recentchange.raw", help="Topic to consume from")
@click.option("--group-id", default="option3-transform", help="Consumer group ID")
@click.option("--output-dir", default="data", help="Directory for parquet output")
@click.option("--batch-size", default=500, type=int, help="Events per batch")
@click.option("--flush-interval", default=30, type=int, help="Max seconds between flushes")
def main(
    brokers: str,
    topic: str,
    group_id: str,
    output_dir: str,
    batch_size: int,
    flush_interval: int,
) -> None:
    """Consume wiki events from Kafka, transform with Polars, write parquet."""
    structlog.configure(
        processors=[
            structlog.dev.ConsoleRenderer(),
        ],
    )

    logger.info(
        "transform_starting",
        brokers=brokers,
        topic=topic,
        group_id=group_id,
        output_dir=output_dir,
    )

    consumer = KafkaConsumer(brokers=brokers, group_id=group_id, topic=topic)
    batch: list[dict] = []
    last_flush = time.monotonic()

    try:
        for event in consumer.events():
            batch.append(event)

            elapsed = time.monotonic() - last_flush
            if len(batch) >= batch_size or elapsed >= flush_interval:
                df = events_to_dataframe(batch)
                write_batch_to_parquet(df, output_dir)
                logger.info("batch_flushed", events=len(batch), elapsed=f"{elapsed:.1f}s")
                batch = []
                last_flush = time.monotonic()
    except KeyboardInterrupt:
        logger.info("transform_shutting_down")
    finally:
        if batch:
            df = events_to_dataframe(batch)
            write_batch_to_parquet(df, output_dir)
            logger.info("final_batch_flushed", events=len(batch))
        consumer.close()


if __name__ == "__main__":
    main()
