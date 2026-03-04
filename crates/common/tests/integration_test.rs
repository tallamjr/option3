use common::config::{AppConfig, KafkaConfig, SseConfig};
use common::models::{EditSummary, WikiEvent};

/// Real edit event captured from the Wikimedia EventStreams SSE endpoint
/// https://stream.wikimedia.org/v2/stream/recentchange on 2026-03-04.
/// User PontiffSulivahn edited the "March 7" article on English Wikipedia.
#[test]
fn deserialise_real_wiki_event() {
    let json = r#"{
        "$schema": "/mediawiki/recentchange/1.0.0",
        "meta": {
            "uri": "https://en.wikipedia.org/wiki/March_7",
            "request_id": "8ee6470b-20c0-4ec6-b242-79db24846f5c",
            "id": "03ab2c4f-a040-4969-b726-75820e071dc7",
            "domain": "en.wikipedia.org",
            "stream": "mediawiki.recentchange",
            "dt": "2026-03-04T21:41:26.006Z"
        },
        "id": 2002470984,
        "type": "edit",
        "namespace": 0,
        "title": "March 7",
        "comment": "Added entries + added references",
        "timestamp": 1772660481,
        "user": "PontiffSulivahn",
        "bot": false,
        "notify_url": "https://en.wikipedia.org/w/index.php?diff=1341753263&oldid=1341730446",
        "minor": false,
        "length": { "old": 80518, "new": 81143 },
        "revision": { "old": 1341730446, "new": 1341753263 },
        "server_url": "https://en.wikipedia.org",
        "server_name": "en.wikipedia.org",
        "server_script_path": "/w",
        "wiki": "enwiki",
        "parsedcomment": "Added entries + added references"
    }"#;

    let event: WikiEvent = serde_json::from_str(json).unwrap();

    assert_eq!(event.id, Some(2002470984));
    assert_eq!(event.event_type.as_deref(), Some("edit"));
    assert_eq!(event.title.as_deref(), Some("March 7"));
    assert_eq!(event.wiki.as_deref(), Some("enwiki"));
    assert_eq!(event.user.as_deref(), Some("PontiffSulivahn"));
    assert_eq!(event.bot, Some(false));
    assert_eq!(event.minor, Some(false));
    assert_eq!(event.meta.domain.as_deref(), Some("en.wikipedia.org"));
    assert_eq!(
        event.meta.id.as_deref(),
        Some("03ab2c4f-a040-4969-b726-75820e071dc7")
    );
    assert_eq!(event.length.as_ref().unwrap().old, Some(80518));
    assert_eq!(event.length.as_ref().unwrap().new, Some(81143));
    assert_eq!(event.revision.as_ref().unwrap().old, Some(1341730446));
    assert_eq!(event.revision.as_ref().unwrap().new, Some(1341753263));
}

/// Real log event captured from Wikimedia EventStreams on 2026-03-04.
/// User Rob.maxwell4655 triggered AbuseFilter 550 on English Wikipedia.
#[test]
fn deserialise_log_event() {
    let json = r#"{
        "$schema": "/mediawiki/recentchange/1.0.0",
        "meta": {
            "uri": "https://en.wikipedia.org/wiki/Teacher_Retirement_System_of_Texas",
            "request_id": "d15899b8-8e21-4d11-801a-e76f0a322a80",
            "id": "7f6b8989-2821-453c-801b-e98c2fe2e897",
            "domain": "en.wikipedia.org",
            "stream": "mediawiki.recentchange",
            "dt": "2026-03-04T21:42:11.457Z"
        },
        "type": "log",
        "namespace": 0,
        "title": "Teacher Retirement System of Texas",
        "comment": "",
        "timestamp": 1772660531,
        "user": "Rob.maxwell4655",
        "bot": false,
        "log_id": 0,
        "log_type": "abusefilter",
        "log_action": "hit",
        "log_params": {"action": "edit", "filter": "550", "actions": "tag", "log": 43576646},
        "log_action_comment": "Rob.maxwell4655 triggered filter 550, performing the action \"edit\" on [[Teacher Retirement System of Texas]]. Actions taken: Tag",
        "server_url": "https://en.wikipedia.org",
        "server_name": "en.wikipedia.org",
        "server_script_path": "/w",
        "wiki": "enwiki",
        "parsedcomment": ""
    }"#;

    let event: WikiEvent = serde_json::from_str(json).unwrap();

    assert_eq!(event.event_type.as_deref(), Some("log"));
    assert_eq!(
        event.title.as_deref(),
        Some("Teacher Retirement System of Texas")
    );
    assert_eq!(event.user.as_deref(), Some("Rob.maxwell4655"));
    assert_eq!(event.log_type.as_deref(), Some("abusefilter"));
    assert_eq!(event.log_action.as_deref(), Some("hit"));
    assert_eq!(event.log_id, Some(0));
    assert!(event.log_params.is_some());
    assert!(event.length.is_none());
    assert!(event.revision.is_none());
}

/// Real edit event from Wikimedia Commons on 2026-03-04.
/// User Rathfelder recategorised logos of companies of Venezuela.
#[test]
fn edit_summary_from_wiki_event() {
    let json = r#"{
        "$schema": "/mediawiki/recentchange/1.0.0",
        "meta": {
            "uri": "https://commons.wikimedia.org/wiki/Category:Logos_of_companies_of_Venezuela",
            "request_id": "6ee88888-dd7d-4439-aa3f-05d2df977c3f",
            "id": "d14ab9d8-e41b-4cc2-95b6-90cbd62a0556",
            "domain": "commons.wikimedia.org",
            "stream": "mediawiki.recentchange",
            "dt": "2026-03-04T21:41:25.661Z"
        },
        "id": 3221685411,
        "type": "edit",
        "namespace": 14,
        "title": "Category:Logos of companies of Venezuela",
        "comment": "removed [[Category:Logos of Venezuela]]; added [[Category:Logos of organizations of Venezuela]]",
        "timestamp": 1772660484,
        "user": "Rathfelder",
        "bot": false,
        "minor": true,
        "length": { "old": 203, "new": 220 },
        "revision": { "old": 891644618, "new": 1175962618 },
        "server_url": "https://commons.wikimedia.org",
        "server_name": "commons.wikimedia.org",
        "server_script_path": "/w",
        "wiki": "commonswiki"
    }"#;

    let event: WikiEvent = serde_json::from_str(json).unwrap();
    let summary = EditSummary::from(&event);

    assert_eq!(summary.id, Some(3221685411));
    assert_eq!(summary.wiki, "commonswiki");
    assert_eq!(summary.user, "Rathfelder");
    assert!(!summary.bot);
    assert_eq!(summary.event_type, "edit");
    assert_eq!(summary.timestamp, Some(1772660484));
    // 220 - 203 = 17 bytes size change
    assert_eq!(summary.size_change, Some(17));
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
