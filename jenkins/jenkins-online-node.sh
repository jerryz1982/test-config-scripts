#!/bin/bash
URL=$1
NODE_NAME=$2
java -jar /home/jenkins/scripts/jenkins-cli.jar -s ${URL} wait-node-online ${NODE_NAME} 
