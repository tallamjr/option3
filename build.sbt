// Package Information

name := "option3" //
organization := "com.github.tallamjr"
version := "0.1"
scalaVersion := "2.11.0"

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
