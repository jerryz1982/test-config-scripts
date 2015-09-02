#!/bin/bash

JENKINS_URL=$1
NODE_NAME=$2
NODE_SLAVE_HOME='/home/jenkins'
EXECUTORS=1
HOST=$3
SSH_PORT=22
CRED_ID=$4
LABELS=devstack
USERID=anonymous

cat <<EOF | java -jar /home/jenkins/scripts/jenkins-cli.jar -s $1 create-node $2
<slave>
  <name>${NODE_NAME}</name>
  <description></description>
  <remoteFS>${NODE_SLAVE_HOME}</remoteFS>
  <numExecutors>${EXECUTORS}</numExecutors>
  <mode>NORMAL</mode>
  <retentionStrategy class="hudson.slaves.RetentionStrategy$Always"/>
  <launcher class="hudson.plugins.sshslaves.SSHLauncher" plugin="ssh-slaves@1.9">
    <host>${HOST}</host>
    <port>${SSH_PORT}</port>
    <credentialsId>${CRED_ID}</credentialsId>
  </launcher>
  <label>${LABELS}</label>
  <nodeProperties/>
  <userId>${USERID}</userId>
</slave>
EOF
