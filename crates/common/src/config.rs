/// Kafka / RedPanda broker configuration.
#[derive(Debug, Clone)]
pub struct KafkaConfig {
    pub brokers: String,
    pub topic: String,
    pub group_id: String,
}

impl Default for KafkaConfig {
    fn default() -> Self {
        Self {
            brokers: "localhost:19092".to_string(),
            topic: "wiki.recentchange.raw".to_string(),
            group_id: "option3-transform".to_string(),
        }
    }
}

/// SSE stream source configuration.
#[derive(Debug, Clone)]
pub struct SseConfig {
    pub url: String,
    pub wikis: Vec<String>,
}

impl Default for SseConfig {
    fn default() -> Self {
        Self {
            url: "https://stream.wikimedia.org/v2/stream/recentchange".to_string(),
            wikis: vec![
                "enwiki".to_string(),
                "wikidatawiki".to_string(),
                "commonswiki".to_string(),
            ],
        }
    }
}

/// REST API server configuration.
#[derive(Debug, Clone)]
pub struct ApiConfig {
    pub host: String,
    pub port: u16,
}

impl Default for ApiConfig {
    fn default() -> Self {
        Self {
            host: "0.0.0.0".to_string(),
            port: 3000,
        }
    }
}

/// Parquet storage configuration.
#[derive(Debug, Clone)]
pub struct StorageConfig {
    pub parquet_dir: String,
}

impl Default for StorageConfig {
    fn default() -> Self {
        Self {
            parquet_dir: "data".to_string(),
        }
    }
}

/// Top-level application configuration combining all sub-configs.
#[derive(Debug, Clone, Default)]
pub struct AppConfig {
    pub kafka: KafkaConfig,
    pub sse: SseConfig,
    pub api: ApiConfig,
    pub storage: StorageConfig,
}
