import os
import time
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import from_json, col


def logLevel(spark):
    # REF: https://stackoverflow.com/questions/25193488/how-to-turn-off-info-logging-in-spark
    sc = spark.sparkContext
    log4jLogger = sc._jvm.org.apache.log4j
    log4jLogger.Logger.getLogger("org").setLevel(log4jLogger.Level.ERROR)
    log = log4jLogger.LogManager.getLogger(__name__)
    log.warn("Custom Warning")


spark = SparkSession.builder \
    .master("local[*]") \
    .appName("Demo") \
    .getOrCreate()


logLevel(spark)

spark.sparkContext.setLogLevel("ERROR")

print(spark.range(5000).where("id > 500").selectExpr("sum(id)").collect())

df = spark.read.format("csv") \
    .option("header", "true") \
    .option("mode", "FAILFAST") \
    .load("file:" + os.getenv("OPTION3_HOME") + "/data/training_set.csv")

df.show(5)

df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "twitter_status_connect") \
    .load()


df.printSchema()

topicSchema = StructType() \
                .add("schema", StringType()) \
                .add("payload", StringType())


tweets = df.select(col("key").cast("string"),
            from_json(col("value").cast("string"), topicSchema))

print(type(tweets))

streamQuery = tweets.writeStream\
                    .format("memory")\
                    .queryName("tweets_data")\
                    .outputMode("append")\
                    .start()


print(streamQuery.isActive)

for seconds in range(10):
    print("Refreshing....")
    spark.sql("""
      SELECT *
      FROM tweets_data
      """)\
      .show(5, truncate=False)
    time.sleep(2)

streamQuery.stop()
# streamQuery.awaitTermination()
