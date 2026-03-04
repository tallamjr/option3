use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::response::Response;
use futures::StreamExt;
use tracing::{info, warn};

/// Upgrade an HTTP connection to a WebSocket.
pub async fn ws_handler(ws: WebSocketUpgrade) -> Response {
    ws.on_upgrade(handle_socket)
}

async fn handle_socket(mut socket: WebSocket) {
    info!("WebSocket client connected");

    if socket
        .send(Message::Text(
            r#"{"type":"welcome","message":"connected to option3 WebSocket"}"#.into(),
        ))
        .await
        .is_err()
    {
        return;
    }

    // Echo-based scaffolding: echo back received messages
    while let Some(Ok(msg)) = socket.next().await {
        match msg {
            Message::Text(text) => {
                if socket.send(Message::Text(text)).await.is_err() {
                    break;
                }
            }
            Message::Close(_) => {
                info!("WebSocket client disconnected");
                break;
            }
            _ => {}
        }
    }

    warn!("WebSocket connection closed");
}
