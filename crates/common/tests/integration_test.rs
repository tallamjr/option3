use common::config::{AppConfig, KafkaConfig, SseConfig};
use common::models::{EditSummary, WikiEvent};

#[test]
fn deserialise_real_wiki_event() {
    let json = r#"{
        "$schema": "/mediawiki/recentchange/1.0.1",
        "meta": {
            "uri": "https://en.wikipedia.org/wiki/Albert_Einstein",
            "request_id": "abc-123",
            "id": "evt-456",
            "dt": "2024-03-04T12:00:00Z",
            "domain": "en.wikipedia.org",
            "stream": "mediawiki.recentchange"
        },
        "id": 1234567890,
        "type": "edit",
        "namespace": 0,
        "title": "Albert Einstein",
        "comment": "Fixed citation format",
        "timestamp": 1709553600,
        "user": "ExampleEditor",
        "bot": false,
        "minor": false,
        "wiki": "enwiki",
        "server_name": "en.wikipedia.org",
        "server_url": "https://en.wikipedia.org",
        "server_script_path": "/w",
        "length": { "old": 15000, "new": 15200 },
        "revision": { "old": 100, "new": 101 }
    }"#;

    let event: WikiEvent = serde_json::from_str(json).unwrap();

    assert_eq!(event.id, Some(1234567890));
    assert_eq!(event.event_type.as_deref(), Some("edit"));
    assert_eq!(event.title.as_deref(), Some("Albert Einstein"));
    assert_eq!(event.wiki.as_deref(), Some("enwiki"));
    assert_eq!(event.bot, Some(false));
    assert_eq!(event.meta.domain.as_deref(), Some("en.wikipedia.org"));
    assert_eq!(event.length.as_ref().unwrap().old, Some(15000));
    assert_eq!(event.length.as_ref().unwrap().new, Some(15200));
    assert_eq!(event.revision.as_ref().unwrap().old, Some(100));
    assert_eq!(event.revision.as_ref().unwrap().new, Some(101));
}

#[test]
fn deserialise_log_event() {
    let json = r#"{
        "$schema": "/mediawiki/recentchange/1.0.1",
        "meta": {
            "dt": "2024-03-04T12:05:00Z",
            "domain": "en.wikipedia.org",
            "stream": "mediawiki.recentchange"
        },
        "id": 9999,
        "type": "log",
        "namespace": 2,
        "title": "User:SpamAccount",
        "comment": "Blocked for spam",
        "timestamp": 1709553900,
        "user": "AdminUser",
        "bot": false,
        "wiki": "enwiki",
        "server_name": "en.wikipedia.org",
        "log_id": 555,
        "log_type": "block",
        "log_action": "block"
    }"#;

    let event: WikiEvent = serde_json::from_str(json).unwrap();

    assert_eq!(event.event_type.as_deref(), Some("log"));
    assert_eq!(event.log_type.as_deref(), Some("block"));
    assert_eq!(event.log_action.as_deref(), Some("block"));
    assert_eq!(event.log_id, Some(555));
}

#[test]
fn edit_summary_from_wiki_event() {
    let json = r#"{
        "$schema": "/mediawiki/recentchange/1.0.1",
        "meta": { "dt": "2024-03-04T12:00:00Z" },
        "id": 42,
        "type": "edit",
        "title": "Rust (programming language)",
        "user": "RustFan",
        "bot": false,
        "wiki": "enwiki",
        "timestamp": 1709553600,
        "length": { "old": 5000, "new": 5500 }
    }"#;

    let event: WikiEvent = serde_json::from_str(json).unwrap();
    let summary = EditSummary::from(&event);

    assert_eq!(summary.wiki, "enwiki");
    assert_eq!(summary.user, "RustFan");
    assert!(!summary.bot);
    assert_eq!(summary.size_change, Some(500));
}

#[test]
fn default_config_has_sensible_values() {
    let config = AppConfig::default();

    assert_eq!(config.kafka.brokers, "localhost:19092");
    assert_eq!(config.kafka.topic, "wiki.recentchange.raw");
    assert_eq!(config.api.port, 3000);
    assert!(config.sse.wikis.contains(&"enwiki".to_string()));
}

#[test]
fn kafka_config_defaults() {
    let config = KafkaConfig::default();
    assert_eq!(config.group_id, "option3-transform");
}

#[test]
fn sse_config_defaults() {
    let config = SseConfig::default();
    assert_eq!(
        config.url,
        "https://stream.wikimedia.org/v2/stream/recentchange"
    );
    assert_eq!(config.wikis.len(), 3);
}
