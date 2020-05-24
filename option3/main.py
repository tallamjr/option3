import os
from pyspark.sql import SparkSession
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

