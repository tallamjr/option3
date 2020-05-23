package com.databricks.example

import org.apache.log4j.{Logger, Level}
import org.apache.spark.sql.SparkSession

object StreamingExample extends Serializable {
  def main(args: Array[String]) = {

    Logger.getLogger("org").setLevel(Level.ERROR)

    val spark = SparkSession
      .builder()
      .appName("Spark Streaming Example")
      .getOrCreate()
    import spark.implicits._

    // in Scala
    val static = spark.read.json("./data/activity-data/")
    val dataSchema = static.schema


    // COMMAND ----------

    // in Scala
    val streaming = spark.readStream.schema(dataSchema)
      .option("maxFilesPerTrigger", 1).json("./data/activity-data")


    // COMMAND ----------

    // in Scala
    val activityCounts = streaming.groupBy("gt").count()


    // COMMAND ----------

    spark.conf.set("spark.sql.shuffle.partitions", 5)


    // COMMAND ----------

    // in Scala
    val activityQuery = activityCounts.writeStream.queryName("activity_counts")
      .format("memory").outputMode("complete")
      .start()


    // COMMAND ----------

    spark.streams.active


    // COMMAND ----------

    // in Scala
    for( i <- 1 to 10 ) {
        println("Refreshing....")
        spark.sql("SELECT * FROM activity_counts").show()
        Thread.sleep(1000)
    }

    // COMMAND ----------

    activityQuery.awaitTermination()

  }
}
