use anyhow::Result;
use common::error::Option3Error;
use common::models::WikiEvent;
use futures::StreamExt;
use rdkafka::config::ClientConfig;
use rdkafka::producer::{FutureProducer, FutureRecord};
use reqwest_eventsource::{Event, EventSource};
use std::time::Duration;
use tracing::{debug, error, info, warn};

/// Create a Kafka/RedPanda producer configured for throughput with safety.
pub fn create_producer(brokers: &str) -> Result<FutureProducer> {
    let producer: FutureProducer = ClientConfig::new()
        .set("bootstrap.servers", brokers)
        .set("compression.type", "snappy")
        .set("linger.ms", "5")
        .set("batch.num.messages", "1000")
        .set("enable.idempotence", "true")
        .set("acks", "all")
        .create()
        .map_err(|e| Option3Error::KafkaProducer(e.to_string()))?;

    Ok(producer)
}

/// Connect to the Wikimedia EventStreams SSE endpoint and produce filtered
/// events to RedPanda.
pub async fn run_sse_ingestion(
    brokers: &str,
    topic: &str,
    sse_url: &str,
    wikis: &[String],
) -> Result<()> {
    let producer = create_producer(brokers)?;
    info!(brokers, topic, sse_url, "starting SSE ingestion");

    let mut es = EventSource::get(sse_url);

    while let Some(event_result) = es.next().await {
        match event_result {
            Ok(Event::Open) => {
                info!("SSE connection established");
            }
            Ok(Event::Message(msg)) => {
                let event: WikiEvent = match serde_json::from_str(&msg.data) {
                    Ok(e) => e,
                    Err(err) => {
                        debug!(%err, "skipping unparseable SSE message");
                        continue;
                    }
                };

                // Filter to configured wikis
                let wiki = match &event.wiki {
                    Some(w) => w.clone(),
                    None => continue,
                };

                if !wikis.is_empty() && !wikis.iter().any(|w| w == &wiki) {
                    continue;
                }

                let key = format!(
                    "{}:{}",
                    wiki,
                    event.id.map(|id| id.to_string()).unwrap_or_default()
                );

                let payload = match serde_json::to_string(&event) {
                    Ok(p) => p,
                    Err(err) => {
                        warn!(%err, "failed to serialise event");
                        continue;
                    }
                };

                let record = FutureRecord::to(topic).key(&key).payload(&payload);

                if let Err((err, _)) = producer.send(record, Duration::from_secs(5)).await {
                    error!(%err, "failed to produce message to RedPanda");
                }
            }
            Err(err) => {
                warn!(%err, "SSE stream error, reconnecting");
            }
        }
    }

    Err(Option3Error::SseStreamEnded.into())
}
