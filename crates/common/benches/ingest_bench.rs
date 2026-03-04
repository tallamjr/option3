#![allow(unused)]

use common::models::WikiEvent;
use std::hint::black_box;

fn bench_deserialise_wiki_event() {
    let json = r#"{
        "$schema": "/mediawiki/recentchange/1.0.1",
        "meta": {
            "uri": "https://en.wikipedia.org/wiki/Test",
            "request_id": "req-1",
            "id": "evt-1",
            "dt": "2024-03-04T12:00:00Z",
            "domain": "en.wikipedia.org",
            "stream": "mediawiki.recentchange"
        },
        "id": 123456,
        "type": "edit",
        "namespace": 0,
        "title": "Test Article",
        "comment": "Test edit",
        "timestamp": 1709553600,
        "user": "BenchUser",
        "bot": false,
        "minor": false,
        "wiki": "enwiki",
        "server_name": "en.wikipedia.org",
        "length": { "old": 1000, "new": 1100 },
        "revision": { "old": 50, "new": 51 }
    }"#;

    for _ in 0..10_000 {
        let event: WikiEvent = black_box(serde_json::from_str(json).unwrap());
        black_box(&event);
    }
}

fn main() {
    bench_deserialise_wiki_event();
}
