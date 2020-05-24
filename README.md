# option3 - #

                   __  _            _____
      ____  ____  / /_(_)___  ____ |__  /
     / __ \/ __ \/ __/ / __ \/ __ \ /_ <
    / /_/ / /_/ / /_/ / /_/ / / / /__/ /
    \____/ .___/\__/_/\____/_/ /_/____/
        /_/

## Directory Structure

```bash
.
├── LICENSE
├── README.md
├── bin
├── build.sbt
├── data
├── environment.yml
├── libs
├── notebooks
├── project
├── pytest.ini
├── requirements.txt
├── sbin
├── setup.py
├── option3
├── src
└── target

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