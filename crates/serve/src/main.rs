use anyhow::Result;
use clap::Parser;
use polars::prelude::*;
use std::path::Path;
use std::sync::{Arc, RwLock};
use tracing::{info, warn};

use serve::routes::{build_router, AppState};

#[derive(Parser, Debug)]
#[command(
    name = "serve",
    about = "REST API and WebSocket server for option3 analytics"
)]
struct Args {
    /// Host address to bind to
    #[arg(long, default_value = "0.0.0.0")]
    host: String,

    /// Port to listen on
    #[arg(long, default_value_t = 3000)]
    port: u16,

    /// Directory containing parquet files
    #[arg(long, default_value = "data")]
    parquet_dir: String,
}

fn load_parquet(parquet_dir: &str) -> Option<DataFrame> {
    let path = Path::new(parquet_dir);
    if !path.exists() {
        warn!(%parquet_dir, "parquet directory does not exist");
        return None;
    }

    let pattern = format!("{}/*.parquet", parquet_dir);
    match LazyFrame::scan_parquet(&pattern, Default::default()) {
        Ok(lf) => match lf.collect() {
            Ok(df) => {
                info!(rows = df.height(), cols = df.width(), "loaded parquet data");
                Some(df)
            }
            Err(err) => {
                warn!(%err, "failed to collect parquet data");
                None
            }
        },
        Err(err) => {
            warn!(%err, "no parquet files found");
            None
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "serve=info,tower_http=debug".into()),
        )
        .init();

    let args = Args::parse();
    info!(?args, "serve starting");

    let df = load_parquet(&args.parquet_dir);
    let state = AppState {
        df: Arc::new(RwLock::new(df)),
        parquet_dir: args.parquet_dir,
    };

    let app = build_router(state);
    let addr = format!("{}:{}", args.host, args.port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    info!(%addr, "listening");

    axum::serve(listener, app).await?;
    Ok(())
}
