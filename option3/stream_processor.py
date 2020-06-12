import os
from time import sleep

from pyspark.sql.types import ArrayType, FloatType, LongType
import pyspark.sql.functions as psf
from pyspark.sql import SparkSession


def parseJSONCols(df, *cols, sanitize=True):
    """Auto infer the schema of a json column and parse into a struct.
    Note: This code has been lifted verbatem from :
        https://stackoverflow.com/a/51072232/4521950

    rdd-based schema inference works if you have well-formatted JSON,
    like ``{"key": "value", ...}``, but breaks if your 'JSON' is just a
    string (``"data"``) or is an array (``[1, 2, 3]``). In those cases you
    can fix everything by wrapping the data in another JSON object
    (``{"key": [1, 2, 3]}``). The ``sanitize`` option (default True)
    automatically performs the wrapping and unwrapping.

    The schema inference is based on this
    `SO Post <https://stackoverflow.com/a/45880574)/>`_.

    Parameters
    ----------
    df : `pyspark Dataframe`
        Dataframe containing the JSON cols.
    *cols : `str(s)`
        Names of the columns containing JSON.
    sanitize : `boolean`
        Flag indicating whether you'd like to sanitize your records
        by wrapping and unwrapping them in another JSON object layer.

    Returns
    -------
    res : `pyspark Dataframe`
        A dataframe with the decoded columns.
    """
    res = df
    for i in cols:
        # sanitize if requested.
        if sanitize:
            res = (
                res.withColumn(
                    i,
                    psf.concat(psf.lit('{"data": '), i, psf.lit('}'))
                )
            )
        # infer schema and apply it
        schema = spark.read.json(res.rdd.map(lambda x: x[i])).schema
        res = res.withColumn(i, psf.from_json(psf.col(i), schema))

        # unpack the wrapped object if needed
        if sanitize:
            res = res.withColumn(i, psf.col(i).data)
    return res


def logLevel(spark):
    """ Set log level of log4j to only show upon ERROR

    Parameters
    ----------
    spark : `sparkSession`
    Current spark session for application

    Notes
    -----
    Ref : https://stackoverflow.com/questions/25193488/how-to-turn-off-info-logging-in-spark

    Examples
    ----------
    >>> ...
    20/06/08 15:10:01 WARN __main__: Custom Warning
    """

    sc = spark.sparkContext
    sc.setLogLevel("ERROR")
    log4jLogger = sc._jvm.org.apache.log4j
    log4jLogger.Logger.getLogger("org").setLevel(log4jLogger.Level.ERROR)
    log = log4jLogger.LogManager.getLogger(__name__)
    log.warn("Custom Warning")


def sparkSession(appName: str) -> SparkSession:
    """ Init spark session with application name and set number of cores via master. If one is
    already created with the same name, that one will be used, otherwise a new session is created.

    Parameters
    ----------
    appName : `str`
        Name of cuurent application and spark session

    Returns
    -------
    spark : `sparkSession`
        SparkSession. Spark Context accessiable via spark.sparkContext

    Examples
    ----------
    >>> spark = sparkSession("demo")
    >>> spark.sparkContext.getConf().get('spark.app.name')
    'demo'
    >>> spark.sparkContext.getConf().get('spark.master')
    'local[*]'
    >>>
    """
    master = os.getenv("SPARK_MASTER", "local[*]")

    spark = SparkSession.builder \
        .master(master) \
        .appName(appName) \
        .getOrCreate()

    return spark


spark = sparkSession("demo")

logLevel(spark)

print(spark.range(5000).where("id > 500").selectExpr("sum(id)").collect())

df = spark.read.format("csv") \
    .option("header", "true") \
    .load("file:" + os.getenv("OPTION3_HOME") + "/data/training_set.csv")

df.show(5)

df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("startingOffsets", "latest") \
    .option("subscribe", "twitter_tweets") \
    .load() \
    .selectExpr("CAST(value AS STRING) as tweets")


df.printSchema()

tweets = df.writeStream \
                    .format("memory") \
                    .queryName("tweeters") \
                    .outputMode("update") \
                    .start()


df = spark.sql(""" SELECT * FROM tweeters """)

df.show()

while df.count() < 2:
    sleep(5)    # Time in seconds

df.show()

ddf = parseJSONCols(df, 'tweets', sanitize=True)
ddf.printSchema()

print(tweets.isActive)

ddf.show()

ddf.select("tweets.created_at", "tweets.coordinates.coordinates",
        "tweets.user.followers_count").show(truncate=False)

ddf.select("tweets.created_at", "tweets.coordinates.coordinates", "tweets.user.followers_count",
        "tweets.quoted_status.text").show(truncate=False)

print(ddf.count())

ddf.select("tweets.created_at", "tweets.coordinates.coordinates", "tweets.user.followers_count",
        "tweets.extended_tweet.full_text") \
                .where(psf.col("tweets.coordinates").isNotNull()) \
                .show(truncate=False)


def multiply_func(a):
    return a * 2


multiply = psf.pandas_udf(multiply_func, returnType=LongType())


@psf.pandas_udf(ArrayType(FloatType()))
def lat(v: float):
    """ Extract first column from 2D matrix

    Parameters
    ----------
    v : `float`
    The 2D vector for which to extract item

    Returns
    -------
    Single value contained inside vecotr

    Examples
    ----------
    >>> ldd = dd.withColumn("latitude", lat(psf.col("coordinates")))
    ...
    """
    return v.apply(lambda x: x[1:])


@psf.pandas_udf(ArrayType(FloatType()))
def lond(v):
    """ Extract second column from 2D matrix

    Parameters
    ----------
    v : `float`
    The 2D vector for which to extract item

    Returns
    -------
    Single value contained inside vecotr

    Examples
    ----------
    >>> ldd = dd.withColumn("latitude", lat(psf.col("coordinates")))
    ...
    """
    return v.apply(lambda x: x[:1])


dd = ddf.select("tweets.created_at", "tweets.coordinates.coordinates",
                "tweets.user.followers_count", "tweets.extended_tweet.full_text") \
                .where(psf.col("tweets.coordinates").isNotNull()) \
                .where(psf.col("tweets.extended_tweet.full_text").isNotNull())

dd.show()

dd.withColumn("follower_count_times_two", multiply(psf.col("followers_count"))).show()

ldd = dd.withColumn("latitude", lat(psf.col("coordinates")))
lldd = ldd.withColumn("longditude", lond(psf.col("coordinates")))
lldd.show()

print(lldd.count())

lldd_pdf = lldd.toPandas()

print(lldd_pdf['latitude'].tolist()[0].item())

lati_series = lldd_pdf['latitude'].transform(lambda x: x.item())
longd_series = lldd_pdf['longditude'].transform(lambda x: x.item())

lldd_pdf['llat'] = lldd_pdf['latitude'].transform(lambda x: x.item())
lldd_pdf['llong'] = lldd_pdf['longditude'].transform(lambda x: x.item())

lldd_pdf.head()

tweets.stop()

# df = spark \
#     .readStream \
#     .format("kafka") \
#     .option("kafka.bootstrap.servers", "localhost:9092") \
#     .option("subscribe", "twitter_status_connect") \
#     .load()


# df.printSchema()

# topicSchema = StructType() \
#                 .add("schema", StringType()) \
#                 .add("payload", StringType())


# tweets = df.select(col("key").cast("string"),
#             from_json(col("value").cast("string"), topicSchema))

# print(type(tweets))

# streamQuery = tweets.writeStream\
#                     .format("memory")\
#                     .queryName("tweets_data")\
#                     .outputMode("append")\
#                     .start()


# print(streamQuery.isActive)

# for seconds in range(10):
#     print("Refreshing....")
#     spark.sql("""
#       SELECT *
#       FROM tweets_data
#       """)\
#       .show(5)
#     time.sleep(2)

# print(type(spark.sql(""" SELECT * FROM tweets_data """)))

# streamQuery.stop()
# # streamQuery.awaitTermination()
