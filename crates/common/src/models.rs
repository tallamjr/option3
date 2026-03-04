use serde::{Deserialize, Serialize};

/// Metadata envelope present on all Wikimedia EventStreams events.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventMeta {
    pub uri: Option<String>,
    pub request_id: Option<String>,
    pub id: Option<String>,
    /// ISO-8601 timestamp set by the event producer.
    pub dt: Option<String>,
    pub domain: Option<String>,
    pub stream: Option<String>,
}

/// Revision IDs for the page change.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Revision {
    pub new: Option<i64>,
    pub old: Option<i64>,
}

/// Page length in bytes before and after the change.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Length {
    pub new: Option<i64>,
    pub old: Option<i64>,
}

/// A single recent-change event from the Wikimedia EventStreams SSE endpoint.
///
/// Schema reference: <https://schema.wikimedia.org/repositories/primary/jsonschema/mediawiki/recentchange/latest.yaml>
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WikiEvent {
    /// JSON Schema URI for this event.
    #[serde(rename = "$schema")]
    pub schema: Option<String>,

    /// Event metadata envelope.
    pub meta: EventMeta,

    /// Recent-change ID (rc_id).
    pub id: Option<i64>,

    /// Event type: "edit", "new", "log", "categorize", or "external".
    #[serde(rename = "type")]
    pub event_type: Option<String>,

    /// MediaWiki namespace ID of the affected page.
    pub namespace: Option<i32>,

    /// Full page title including namespace prefix.
    pub title: Option<String>,

    /// Edit summary / comment.
    pub comment: Option<String>,

    /// Unix timestamp of the change.
    pub timestamp: Option<i64>,

    /// Username that made the change.
    pub user: Option<String>,

    /// Whether the change was made by a bot account.
    pub bot: Option<bool>,

    /// Whether the edit was flagged as minor.
    pub minor: Option<bool>,

    /// Whether the change has been patrolled.
    pub patrolled: Option<bool>,

    /// Wiki database identifier (e.g. "enwiki").
    pub wiki: Option<String>,

    /// Server hostname (e.g. "en.wikipedia.org").
    pub server_name: Option<String>,

    /// Canonical server URL.
    pub server_url: Option<String>,

    /// Script path (e.g. "/w").
    pub server_script_path: Option<String>,

    /// Old and new page lengths in bytes.
    pub length: Option<Length>,

    /// Old and new revision IDs.
    pub revision: Option<Revision>,

    // Log-specific fields (present when type = "log")
    pub log_id: Option<i64>,
    pub log_type: Option<String>,
    pub log_action: Option<String>,
    pub log_params: Option<serde_json::Value>,
    pub log_action_comment: Option<String>,
}

/// Lightweight summary of an edit event, suitable for aggregation and API responses.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EditSummary {
    pub id: Option<i64>,
    pub wiki: String,
    pub title: String,
    pub user: String,
    pub bot: bool,
    pub event_type: String,
    pub timestamp: Option<i64>,
    pub size_change: Option<i64>,
}

impl From<&WikiEvent> for EditSummary {
    fn from(event: &WikiEvent) -> Self {
        let size_change = event.length.as_ref().and_then(|l| match (l.new, l.old) {
            (Some(new), Some(old)) => Some(new - old),
            _ => None,
        });

        Self {
            id: event.id,
            wiki: event.wiki.clone().unwrap_or_default(),
            title: event.title.clone().unwrap_or_default(),
            user: event.user.clone().unwrap_or_default(),
            bot: event.bot.unwrap_or(false),
            event_type: event.event_type.clone().unwrap_or_default(),
            timestamp: event.timestamp,
            size_change,
        }
    }
}
