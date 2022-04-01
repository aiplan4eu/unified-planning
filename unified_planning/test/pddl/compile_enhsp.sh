#!/bin/bash
mkdir out
javac -d out -classpath "libs/*" src/planners/*.java src/*.java
jar --create --file enhsp.jar --manifest manifest.mf -C out/ .
mkdir enhsp-dist
cp -r libs/ enhsp-dist/
cp enhsp.jar enhsp-dist/
