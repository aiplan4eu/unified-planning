#!/bin/bash
rm -r out 2> /dev/null
rm -r enhsp-dist 2> /dev/null
javac -d out -classpath "libs/*" src/planners/*.java src/*.java
jar --create --file enhsp.jar --manifest manifest.mf -C out/ .
mkdir enhsp-dist
cp -r libs/ enhsp-dist/
cp enhsp.jar enhsp-dist/
