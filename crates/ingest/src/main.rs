use anyhow::Result;
use clap::Parser;
use tracing::info;

#[derive(Parser, Debug)]
#[command(name = "ingest", about = "Wikimedia SSE to RedPanda ingestion service")]
struct Args {
    /// Kafka/RedPanda broker addresses
    #[arg(long, default_value = "localhost:19092")]
    brokers: String,

    /// Topic to produce events to
    #[arg(long, default_value = "wiki.recentchange.raw")]
    topic: String,

    /// SSE stream URL
    #[arg(
        long,
        default_value = "https://stream.wikimedia.org/v2/stream/recentchange"
    )]
    sse_url: String,

    /// Wiki databases to include (empty = all)
    #[arg(long, value_delimiter = ',', default_values_t = vec![
        "enwiki".to_string(),
        "wikidatawiki".to_string(),
        "commonswiki".to_string(),
    ])]
    wikis: Vec<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "ingest=info".into()),
        )
        .init();

    let args = Args::parse();
    info!(?args, "ingest starting");

    tokio::select! {
        result = ingest::sse::run_sse_ingestion(
            &args.brokers,
            &args.topic,
            &args.sse_url,
            &args.wikis,
        ) => {
            result
        }
        _ = tokio::signal::ctrl_c() => {
            info!("received Ctrl+C, shutting down");
            Ok(())
        }
    }
}
