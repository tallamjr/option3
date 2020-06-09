# Copyright 2020 A. A. Research
# Author: Tarek Allam Jr.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# REF: https://www.bmc.com/blogs/working-streaming-twitter-data-using-kafka/
# bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1
# --topic trump
import os

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from kafka import KafkaProducer, KafkaClient

access_token = os.getenv("ACCESSTOKEN", "")
access_token_secret = os.getenv("ACCESSTOKENSECRET", "")
consumer_key = os.getenv("CONSUMERKEY", "")
consumer_secret = os.getenv("CONSUMERSECRET", "")


class StdOutListener(StreamListener):

    def on_data(self, data):
        producer.send_messages("london", data.encode('utf-8'))
        print(data)
        return True

    def on_error(self, status):
        print(status)


kafka = KafkaClient("localhost:9092")
producer = KafkaProducer(kafka)

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

stream = Stream(auth, StdOutListener())

stream.filter(track="london")
