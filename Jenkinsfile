pipeline {
  agent any

  stages {
    stage('Build') {
      steps {
        echo 'Building..'
      }
    }
    stage('Check User') {
      steps {
        script {
          sh "whoami"
          sh "file ${WORKSPACE}/scripts/jira/jira.py"
        }
      }
    }
    stage('requests') {
      steps {
        sh '''
        python3 -m venv venv
        . venv/bin/activate
        
        '''
      }
    }
  }

  post {
    success {
      script {
        updateJiraIssues('SUCCESS')
        echo "SUCCESS"
      }
    }
    failure {
      script {
        updateJiraIssues('FAILURE')
        echo "FAILURE"
      }
    }
  }
}

def getBranchName() {
  String branch_name = scm.branches[0].name.split('/')[1]
  return branch_name
}

def updateJiraIssues(buildResult) {
  def issueKeys = getIssuesFromChanges()
  if (issueKeys.isEmpty()) {
    echo "JIRA Issue Keys not found in commit messages. Skip this step."
    return
  }
  echo "Target issues: ${issueKeys}"

  def targetVersion = getBranchName()
  echo "Target version: ${targetVersion}"
  withCredentials([
    string(credentialsId: 'JIRA_API_TOKEN', variable: 'PASSWORD'),
    string(credentialsId: 'JIRA_EMAIL_CREDENTIAL_ID', variable: 'USERNAME')
  ]) {
    sh "source ./venv/bin/activate;python3 ${WORKSPACE}/scripts/jira/jira.py '${issueKeys}' '${buildNumber}:${buildResult}' ${targetVersion} $USERNAME $PASSWORD"
  }
}

def getIssuesFromChanges() {
  def changeLogSets = getPreviousFaildBuilds()
  echo "previous size: ${changeLogSets.size()}"
  currentBuild.changeSets.each { cs -> changeLogSets.add(cs) }
  def issueKeys = []

  echo "current size: ${changeLogSets.size()}"

  for (int i = 0; i < changeLogSets.size(); i++) {
    echo "HERE1"
    def entries = changeLogSets[i].items
    echo "HERE2"
    echo "entries: ${entries} / ${entries.length}"
    for (int j = 0; j < entries.length; j++) {
      echo "????"
      def commitMsg = entries[j].msg
      echo "commitMsg: ${commitMsg}"
      def matcher = commitMsg =~ /(SS-\d+)/
      if (matcher) {
          issueKeys.addAll(matcher.collect { it[1] })
      }
    }
  }
  return issueKeys.unique()
}

def getSuccessfulBuildID() {
  def lastSuccessfulBuildID = 0
  def build = currentBuild.previousBuild
  echo "currentBuild: ${currentBuild}"
  echo "buildNumber: ${currentBuild.number}"
  // while (build != null) {
  //   if (build.result == "SUCCESS") {
  //     lastSuccessfulBuildID = build.id as Integer
  //     break
  //   }
  //   build = build.previousBuild
  // }
  // return lastSuccessfulBuildID
}

def getPreviousFaildBuilds() {
  def build = currentBuild.previousBuild
  def changeSets = []
  while (build != null) {
    if (build.result == "SUCCESS") {
      break
    }
    build.changeSets.each { changeSet -> changeSets.add(changeSet) }
    build = build.previousBuild
  }

  return changeSets
}