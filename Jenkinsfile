pipeline {
  agent any

  environment {
    JIRA_REST_API = 'https://sippysoft.atlassian.net/rest/api/3'
    // COMMITTED_TO_FIELD_ID = 'customfield_11400'
  }

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
        }
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
  def issueKeys = getIssueFromChanges()
  if (issueKeys.isEmpty()) {
    echo "JIRA Issue Keys not found in commit messages. Skip this step."
    return
  }
  echo "Target issues: ${issueKeys}"

  def targetVersion = getBranchName()
  echo "Target version: ${targetVersion}"

  for (issueKey in issueKeys) {
    echo "Processing JIRA issue: ${issueKey}"

    sh "${WORKSPACE}/scripts/jira/jira.py ${issueKey} ${buildResult} ${targetVersion}"
  }
}

def getIssueFromChanges() {
  def changeLogSets = currentBuild.changeSets
  def issueKeys = []

  for (int i = 0; i < changeLogSets.size(); i++) {
    def entries = changeLogSets[i].items
    for (int j = 0; j < entries.length; j++) {
      def commitMsg = entries[j].msg
      def matcher = commitMsg =~ /(SS-\d+)/
      if (matcher) {
          issueKeys.addAll(matcher.collect { it[1] })
      }
    }
  }
  return issueKeys.unique()
}
