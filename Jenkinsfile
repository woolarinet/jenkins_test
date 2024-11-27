pipeline {
  agent any

  environment {
    JIRA_EMAIL = credentials('JIRA_EMAIL_CREDENTIAL_ID')
    JIRA_API_TOKEN = credentials('JIRA_API_TOKEN')
  }

  stages {
    stage('Build') {
      steps {
        echo 'Building..'
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
  def issueKeys = getTicketNumberFromChanges()
  if (issueKeys.isEmpty()) {
    echo "JIRA Issue Keys not found in commit messages. Skip this step."
    return
  }
  echo "Target issues: ${issueKeys}"

  def committedBranch = getBranchName()
  echo "Commited to ${committedBranch}"
}

def getTicketNumberFromChanges() {
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