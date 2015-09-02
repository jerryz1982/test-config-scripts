#!/bin/bash
URL=$1
NODE_NAME=$2
java -jar /home/jenkins/scripts/jenkins-cli.jar -s ${URL} delete-node ${NODE_NAME} 
