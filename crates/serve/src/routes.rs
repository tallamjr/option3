use axum::routing::get;
use axum::Router;
use polars::frame::DataFrame;
use std::sync::{Arc, RwLock};
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;

use crate::handlers;
use crate::ws;

/// Shared application state passed to all handlers.
#[derive(Clone)]
pub struct AppState {
    pub df: Arc<RwLock<Option<DataFrame>>>,
    pub parquet_dir: String,
}

/// Build the Axum router with all routes and middleware.
pub fn build_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(handlers::health))
        .route("/api/stats", get(handlers::stats))
        .route("/api/edits/by-wiki", get(handlers::edits_by_wiki))
        .route("/api/editors/top", get(handlers::top_editors))
        .route("/api/activity/by-type", get(handlers::activity_by_type))
        .route("/api/ws", get(ws::ws_handler))
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}
