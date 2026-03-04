use thiserror::Error;

#[derive(Debug, Error)]
pub enum Option3Error {
    #[error("SSE connection failed: {0}")]
    SseConnection(String),

    #[error("SSE stream ended unexpectedly")]
    SseStreamEnded,

    #[error("JSON deserialisation failed: {0}")]
    JsonParse(#[from] serde_json::Error),

    #[error("Kafka producer error: {0}")]
    KafkaProducer(String),

    #[error("Kafka consumer error: {0}")]
    KafkaConsumer(String),

    #[error("Parquet I/O error: {0}")]
    ParquetIo(String),

    #[error("HTTP server error: {0}")]
    HttpServer(String),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error(transparent)]
    Io(#[from] std::io::Error),
}
