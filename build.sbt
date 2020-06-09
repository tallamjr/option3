// Package Information
name := "option3" //
organization := "com.github.tallamjr"

enablePlugins(GitVersioning, GitBranchPrompt)
git.baseVersion := "1.0"
git.useGitDescribe := true
git.formattedShaVersion := git.gitHeadCommit.value map { sha => "v"+git.baseVersion.value+"-"+sha.take(7) }

/* scalaVersion := "2.11.0" */
autoScalaLibrary := true // false = exclude scala-library from dependencies

// Spark Information
val sparkVersion = "2.4.5"

// allows us to include spark packages
resolvers += "bintray-spark-packages" at
  "https://dl.bintray.com/spark-packages/maven/"

resolvers += "Typesafe Simple Repository" at
  "http://repo.typesafe.com/typesafe/simple/maven-releases/"

resolvers += "MavenRepository" at
  "https://mvnrepository.com/"

libraryDependencies ++= Seq(
  // spark core
  "org.apache.spark" %% "spark-core" % sparkVersion,
  "org.apache.spark" %% "spark-sql" % sparkVersion,

  // spark-modules
  "org.apache.spark" %% "spark-graphx" % sparkVersion,
  "org.apache.spark" %% "spark-mllib" % sparkVersion,

  // testing
  "org.scalatest" %% "scalatest" % "3.1.1" % "test",
  "org.scalacheck" %% "scalacheck" % "1.14.3" % "test",

  // logging
  "org.apache.logging.log4j" % "log4j-api" % "2.12.1",
  "org.apache.logging.log4j" % "log4j-core" % "2.12.1"
)
/* Producer */
libraryDependencies += "org.apache.kafka" % "kafka-clients" % "2.0.0" % "compile"
libraryDependencies += "org.lz4" % "lz4-java" % "1.4.1" % "compile"
libraryDependencies += "org.xerial.snappy" % "snappy-java" % "1.1.7.1" % "compile"
libraryDependencies += "org.slf4j" % "slf4j-api" % "1.7.25" % "compile"
libraryDependencies += "org.slf4j" % "slf4j-simple" % "1.7.25" % "compile"
libraryDependencies += "com.twitter" % "hbc-core" % "2.2.0" % "compile"
libraryDependencies += "org.apache.httpcomponents" % "httpclient" % "4.2.5" % "compile"
libraryDependencies += "org.apache.httpcomponents" % "httpcore" % "4.2.4" % "compile"
libraryDependencies += "commons-logging" % "commons-logging" % "1.1.1" % "compile"
libraryDependencies += "commons-codec" % "commons-codec" % "1.6" % "compile"
libraryDependencies += "com.google.guava" % "guava" % "14.0.1" % "compile"
libraryDependencies += "com.twitter" % "joauth" % "6.0.2" % "compile"
libraryDependencies += "com.google.code.findbugs" % "jsr305" % "1.3.9" % "compile"

/* Kafka Streams Filter */
libraryDependencies += "org.apache.kafka" % "kafka-streams" % "2.0.0" % "compile"
libraryDependencies += "org.apache.kafka" % "kafka-clients" % "2.0.0" % "compile"
libraryDependencies += "org.lz4" % "lz4-java" % "1.4.1" % "compile"
libraryDependencies += "org.xerial.snappy" % "snappy-java" % "1.1.7.1" % "compile"
libraryDependencies += "org.apache.kafka" % "connect-json" % "2.0.0" % "compile"
libraryDependencies += "org.apache.kafka" % "connect-api" % "2.0.0" % "compile"
libraryDependencies += "javax.ws.rs" % "javax.ws.rs-api" % "2.1" % "compile"
libraryDependencies += "com.fasterxml.jackson.core" % "jackson-databind" % "2.9.6" % "compile"
libraryDependencies += "com.fasterxml.jackson.core" % "jackson-annotations" % "2.9.0" % "compile"
libraryDependencies += "com.fasterxml.jackson.core" % "jackson-core" % "2.9.6" % "compile"
libraryDependencies += "org.slf4j" % "slf4j-api" % "1.7.25" % "compile"
libraryDependencies += "org.rocksdb" % "rocksdbjni" % "5.7.3" % "compile"
libraryDependencies += "org.slf4j" % "slf4j-simple" % "1.7.25" % "compile"
libraryDependencies += "com.google.code.gson" % "gson" % "2.8.5" % "compile"

mainClass in(Compile, packageBin) := Some("com.databricks.example.MainClass")

// Compiler settings. Use scalac -X for other options and their description.
// See Here for more info http://www.scala-lang.org/files/archive/nightly/docs/manual/html/scalac.html
scalacOptions ++= List("-feature", "-deprecation", "-unchecked", "-Xlint")

// ScalaTest settings.
// Ignore tests tagged as @Slow (they should be picked only by integration test)
testOptions in Test += Tests.Argument(TestFrameworks.ScalaTest, "-l",
  "org.scalatest.tags.Slow", "-u", "target/junit-xml-reports", "-oD", "-eS")

// Native packager options
enablePlugins(JavaAppPackaging)
enablePlugins(DockerPlugin)
// change the name of the project adding the prefix of the user
packageName in Docker := "tallamjr/" +  packageName.value
//the base docker images
dockerBaseImage := "java:8-jre"
//the exposed port
dockerExposedPorts := Seq(9000)
//exposed volumes
dockerExposedVolumes := Seq("/opt/docker/logs")

Compile / unmanagedJars ++= {
val base = baseDirectory.value
val baseDirectories = (base / "libexec" / "connectors" / "kafka-connect-twitter")
val customJars = (baseDirectories ** "*.jar")
customJars.classpath
}

// import NativePackagerHelper._
// mappings in Universal ++= directory("sbin")
