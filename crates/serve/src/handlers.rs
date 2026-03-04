use axum::extract::State;
use axum::http::StatusCode;
use axum::response::Json;
use serde_json::{json, Value};

use crate::routes::AppState;

pub async fn health() -> Json<Value> {
    Json(json!({ "status": "ok" }))
}

pub async fn stats(State(state): State<AppState>) -> Result<Json<Value>, StatusCode> {
    let df = state
        .df
        .read()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    match df.as_ref() {
        Some(df) => Ok(Json(json!({
            "rows": df.height(),
            "columns": df.width(),
        }))),
        None => Ok(Json(json!({
            "rows": 0,
            "columns": 0,
            "message": "no data loaded",
        }))),
    }
}

pub async fn edits_by_wiki(State(state): State<AppState>) -> Result<Json<Value>, StatusCode> {
    let df = state
        .df
        .read()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    match df.as_ref() {
        Some(df) => {
            let wiki_col = df
                .column("wiki")
                .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
            let unique_wikis = wiki_col.n_unique().unwrap_or(0);
            Ok(Json(json!({
                "total_edits": df.height(),
                "unique_wikis": unique_wikis,
            })))
        }
        None => Ok(Json(json!({
            "total_edits": 0,
            "unique_wikis": 0,
        }))),
    }
}

pub async fn top_editors(State(state): State<AppState>) -> Result<Json<Value>, StatusCode> {
    let df = state
        .df
        .read()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    match df.as_ref() {
        Some(df) => {
            let user_col = df
                .column("user")
                .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
            let unique_users = user_col.n_unique().unwrap_or(0);
            Ok(Json(json!({
                "total_edits": df.height(),
                "unique_editors": unique_users,
            })))
        }
        None => Ok(Json(json!({
            "total_edits": 0,
            "unique_editors": 0,
        }))),
    }
}

pub async fn activity_by_type(State(state): State<AppState>) -> Result<Json<Value>, StatusCode> {
    let df = state
        .df
        .read()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    match df.as_ref() {
        Some(df) => {
            let type_col = df
                .column("event_type")
                .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
            let unique_types = type_col.n_unique().unwrap_or(0);
            Ok(Json(json!({
                "total_events": df.height(),
                "unique_types": unique_types,
            })))
        }
        None => Ok(Json(json!({
            "total_events": 0,
            "unique_types": 0,
        }))),
    }
}
