package com.github.tallamjr.tweets

import com.google.gson.JsonParser

import org.apache.kafka.common.protocol.types.Field
import org.apache.kafka.common.serialization.Serdes
import org.apache.kafka.streams.KafkaStreams
import org.apache.kafka.streams.StreamsBuilder
import org.apache.kafka.streams.StreamsConfig
import org.apache.kafka.streams.kstream.KStream

import java.util.Properties

object StreamsFilterTweets {

  def main(args: Array[String]): Unit = {
    // create properties
    val properties: Properties = new Properties()
    properties.setProperty(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG,
      "127.0.0.1:9092")
    properties.setProperty(StreamsConfig.APPLICATION_ID_CONFIG,
      "demo-kafka-streams")
    properties.setProperty(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG,
      classOf[Serdes.StringSerde].getName)
    properties.setProperty(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG,
      classOf[Serdes.StringSerde].getName)
    // create a topology
    val streamsBuilder: StreamsBuilder = new StreamsBuilder()
    // input topic
    val inputTopic: KStream[String, String] =
      streamsBuilder.stream("twitter_tweets")

    // val filteredStream: KStream[String, String] = inputTopic.filter(
    //   (k, jsonTweet) => extractUserFollowersInTweet(jsonTweet) > 10000)
    // filteredStream.to("important_tweets")

    val filteredStream: KStream[String, String] = inputTopic.filter(
      (k, jsonTweet) => extractLocationsInTweet(jsonTweet) == true)
    filteredStream.to("geo_tweets")
    // build the topology
    val kafkaStreams: KafkaStreams =
      new KafkaStreams(streamsBuilder.build(), properties)
    // start our streams application
    kafkaStreams.start()
  }

  private var jsonParser: JsonParser = new JsonParser()

  private def extractUserFollowersInTweet(
    tweetJson: String): java.lang.Integer = // gson library
      try jsonParser
        .parse(tweetJson)
        .getAsJsonObject
        .get("user")
        .getAsJsonObject
        .get("followers_count")
        .getAsInt
        catch {
          case e: NullPointerException => 0
        }

  private def extractLocationsInTweet(
    tweetJson: String): java.lang.Boolean = // gson library
      if (
          !jsonParser
          .parse(tweetJson)
          .getAsJsonObject
          .get("geo")
          .isJsonNull()
        ) {
        try jsonParser
          .parse(tweetJson)
          .getAsJsonObject
          .get("user")
          .getAsJsonObject
          .get("geo_enabled")
          .getAsBoolean
          catch {
            case e: NullPointerException => false
          }
        } else {
          false
        }
}
