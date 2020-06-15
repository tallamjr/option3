    ################################################
    #                                              #
    #                   __  _            _____     #
    #      ____  ____  / /_(_)___  ____ |__  /     #
    #     / __ \/ __ \/ __/ / __ \/ __ \ /_ <      #
    #    / /_/ / /_/ / /_/ / /_/ / / / /__/ /      #
    #    \____/ .___/\__/_/\____/_/ /_/____/       #
    #        /_/                                   #
    #                  * LONDON *                  #
    #                                              #
    ################################################

# OPT + 3 = \#

`option3` is a proof of concept application that is being used to improve my understanding of Kafka
and Spark for developing machine learning data pipelines. Inspired by Kumaran Ponnambalam's [Apache Spark Essential Training: Big Data Engineering](https://www.linkedin.com/learning/apache-spark-essential-training-big-data-engineering/)
and Stephane Maarek's [Kafka for
Beginners](https://www.linkedin.com/learning/learn-apache-kafka-for-beginners) course, I hope to
connect to the Twitter stream of tweets, apply some filtering and transformations, and finally
visualise, in real-time, the processed data.

## Engineering Plan

The idea of this project is to ingest the Twitter stream and push this to a kafka topic (producer),
then use KafkaStream's API to do some kind of filtering and push this filtered stream to a new
topic.  Then, I would like to use Spark Structured Streaming to read this filtered stream and do
some transformations/process each row into a new Spark DataFrame. Finally, I would like to use
Plotly to visualise the location of the tweet on a map of London, with the text of the tweet shown
when hovering over the data point.

It is hoped that building this will allow me to learn several things and develop a
fully fledge data pipeline.

<img src="docs/imgs/option3-plan.svg" alt="drawing"/>

Technologies I hope to use and topics I hope to learn more about:

* Developing a Kafka Producer.
* Using KafkaStreams API
* Using Kafka CLI
* Spark Structure Streaming
* Plotly
* Dash
* Application deployment

## Directory Structure

```bash
.
├── LICENSE                             # Apache 2.0 LICENSE
├── README.md
├── bin -> target/universal/stage/bin   # Symlink to binaries
├── build
├── build.sbt                           # SBT build
├── conf                                # Configuration files
├── data
├── docker                              # Docker-compose files
├── docs
├── environment.yml                     # Anaconda environment
├── lib -> target/universal/stage/lib   # Symlink to compiled library JARs
├── libs                                # Additional JARs
├── mkdocs.yml
├── notebooks                           # Jupyter notebooks
├── option3                             # Python module
├── package                             # Script to build and package option3 with SBT
├── project
├── pytest.ini                          # Pytest configuration
├── requirements.txt
├── sbin                                # Helper development scripts
├── setup.py
├── spark-warehouse
├── src                                 # Scala source code
└── target

15 directories, 9 files
```

## Installation and Development


```bash
$ conda env create -q
$ conda activate option3
```

```bash
$ pip install .
```

## Scala

### Run
```bash
$ sbt clean compile package
$ spark-submit --class com.databricks.example.StreamingExample --master local[*] target/scala-2.11/option3.11-0.1-SNAPSHOT.jar
```

### Test

Test Scala code:
```bash
$ sbt test
```
Or for a single test:
```bash
$ sbt "test:testOnly **.DataFrameExampleTest"
```

With the following plugin:

```bash
addSbtPlugin("org.scoverage" % "sbt-scoverage" % "1.6.1")
```

One can run:

```bash
sbt clean coverage test coverageReport
```

```bash
...
[info] Statement coverage.: 26.79%
[info] Branch coverage....: 100.00%
[info] Coverage reports completed
[info] All done. Coverage was [26.79%]
[success] Total time: 5 s, completed 11-May-2020 13:17:44

```

## Python

### Run

```bash
$ spark-submit option3/main.py
```

### Test

Test Python code:
```bash
$ pytest -vrs tests/
```

```bash
$ cat pytest.ini
[pytest]
filterwarnings =
    ignore::DeprecationWarning
```


To get coverage report:
```bash
(option3) 01:33:01 ✘ ~/github/origin/option3/option3 (master) :: pytest -vrs --cov tests/
================================================= test session starts =================================================
platform darwin -- Python 3.7.6, pytest-5.4.2, py-1.8.1, pluggy-0.13.1 -- /usr/local/anaconda3/envs/option3/bin/python
cachedir: .pytest_cache
spark version -- Spark 2.4.5 (git revision cee4ecb) built for Hadoop 2.7.3 | Build flags: -B -Pmesos -Pyarn -Pkubernetes -Pflume -Psparkr -Pkafka-0-8 -Phadoop-2.7 -Phive -Phive-thriftserver -DzincPort=3036
rootdir: /Users/tallamjr/github/origin/option3, inifile: pytest.ini
plugins: cov-2.9.0, spark-0.6.0
collected 2 items

tests/test_sparkSession.py::test_spark_session_dataframe PASSED                                                 [ 50%]
tests/test_sparkSession.py::test_spark_session_sql PASSED                                                       [100%]

---------- coverage: platform darwin, python 3.7.6-final-0 -----------
Name                         Stmts   Miss  Cover
------------------------------------------------
tests/conftest.py                4      1    75%
tests/test_sparkSession.py      17      2    88%
------------------------------------------------
TOTAL                           21      3    86%


================================================= 2 passed in 12.05s ==================================================
```

## Notebooks

```bash
$ jupyter nbconvert --ExecutePreprocessor.kernel_name=python --ExecutePreprocessor.timeout=600 --to html --execute notebooks/*.ipynb --output-dir notebooks/html/
```

### References

Useful blog posts or online material that can be referenced for this project

* Twitter’s Kafka adoption story:
    https://blog.twitter.com/engineering/en_us/topics/insights/2018/twitters-kafka-adoption-story.html
* Create Beautiful Geomaps with Plotly:
    https://medium.com/analytics-vidhya/plotly-for-geomaps-bb75d1de189f
* The Easiest Way to Deploy Your Dash App for Free
    https://towardsdatascience.com/the-easiest-way-to-deploy-your-dash-app-for-free-f92c575bb69e
* A gentle intro to Dash development
    https://towardsdatascience.com/a-gentle-introduction-to-dash-development-and-deployment-f8b91990d3bd
* How to deploy a simple Python app using nothing but Github and Heroku
    https://medium.com/@austinlasseter/how-to-deploy-a-simple-plotly-dash-app-to-heroku-622a2216eb73
* Successful spark-submits for Python projects.
    https://towardsdatascience.com/successful-spark-submits-for-python-projects-53012ca7405a
* How to setup the Python and Spark environment for development, with good software engineering practices
    https://towardsdatascience.com/how-to-setup-the-pyspark-environment-for-development-with-good-software-engineering-practices-5fb457433a86
* Building Production PySpark Jobs
    https://medium.com/@lubna_22592/building-production-pyspark-jobs-5480d03fd71e
* Best Practices Writing Production-Grade PySpark Jobs
    https://developerzen.com/best-practices-writing-production-grade-pyspark-jobs-cb688ac4d20f
* How To Visualize Spark DataFrames In Scala
    https://towardsdatascience.com/how-to-visualize-spark-dataframe-in-scala-b793265b6c6b
* Fullstack Kafka
    https://levelup.gitconnected.com/fullstack-kafka-e735054adcd6
* The Pros and Cons of Running Apache Spark on Kubernetes
    https://towardsdatascience.com/the-pros-and-cons-of-running-apache-spark-on-kubernetes-13b0e1b17093
* Lessons From Processing 300 Million Messages a Day
    https://medium.com/better-programming/lessons-from-processing-300-million-messages-a-day-5ded130ea1b4
* Beyond Pandas: Spark, Dask, Vaex and other big data technologies battling head to head
    https://towardsdatascience.com/beyond-pandas-spark-dask-vaex-and-other-big-data-technologies-battling-head-to-head-a453a1f8cc13
* PySpark Usage Guide for Pandas with Apache Arrow
    https://spark.apache.org/docs/latest/sql-pyspark-pandas-with-arrow.html
* How to unit test Python Spark jobs
    http://www.nocountryforolddata.com/unit-testing-spark-jobs-in-python.html
* Knowing Spark and Kafka: A 100 Million Events Use-Case
    https://towardsdatascience.com/knowing-pyspark-and-kafka-a-100-million-events-use-case-5910159d08d7
* How To Serve Flask Applications with Gunicorn and Nginx on Ubuntu 18.04
    https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04
* Deploying your Dash app online: Heroku Templates
    https://github.com/plotly/dash-heroku-template
* Deploying Dash Apps
    https://dash.plotly.com/deployment
* Using Plotly Dash
    https://docs.faculty.ai/user-guide/apps/plotly_dash.html
* Real-time Twitter Sentiment Analysis for Brand Improvement and Topic Tracking (Chapter 3/3)
    https://towardsdatascience.com/real-time-twitter-sentiment-analysis-for-brand-improvement-and-topic-tracking-chapter-3-3-3b61b0f488c0
* 7saheelahmed/Real-Time-Twitter-Stream
    https://github.com/7saheelahmed/Real-Time-Twitter-Stream/blob/master/app.py
* Processing Streaming Twitter Data using Kafka and Spark — Part 2: Creating Kafka Twitter stream producer
    https://medium.com/dhoomil-sheta/processing-streaming-twitter-data-using-kafka-and-spark-part-2-creating-kafka-twitter-stream-dccef3418e7
* Continuous deployment using Docker, GitHub Actions, and Web-hooks
    https://levelup.gitconnected.com/automated-deployment-using-docker-github-actions-and-webhooks-54018fc12e32
* Real-time Stream Processing Using Apache Spark Streaming and Apache Kafka on AWS
    https://aws.amazon.com/blogs/big-data/real-time-stream-processing-using-apache-spark-streaming-and-apache-kafka-on-aws/
* Building a real-time prediction pipeline using Spark Structured Streaming and Microservices
    https://towardsdatascience.com/building-a-real-time-prediction-pipeline-using-spark-structured-streaming-and-microservices-626dc20899eb
