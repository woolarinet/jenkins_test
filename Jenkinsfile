pipeline {
  agent any

  environment {
    JIRA_REST_API = 'https://sippysoft.atlassian.net/rest/api/3'
    JIRA_AUTH = credentials('JIRA_AUTH')
    JIRA_EMAIL = credentials('JIRA_EMAIL_CREDENTIAL_ID')
    JIRA_PASS = credentials('JIRA_API_TOKEN')
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

  issueKeys.each { issueKey ->
    echo "Processing JIRA issue: ${issueKey}"

    def currentStatus = getCurrentStatus(issueKey)
    echo "Current Status: ${currentStatus}"
    if (currentStatus != 'Building') {
      echo "The issue's status is not building. Skip this step."
      return
    }
  }
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

def getCurrentStatus(issueKey) {
  withCredentials(
    [string(credentialsId: 'JIRA_API_TOKEN_ID', variable: 'JIRA_API_TOKEN')],
    [string(credentialsId: 'JIRA_EMAIL_CREDENTIAL_ID', variable: 'JIRA_EMAIL_CREDENTIAL_ID')],
    ) {
    def response = sh(
      script: """
      curl --request GET \
          --url '${env.JIRA_REST_API}/issue/${issueKey}' \
          --user '$JIRA_EMAIL_CREDENTIAL_ID:$JIRA_API_TOKEN' \
          --header 'Accept: application/json'
      """,
      returnStdout: true
    ).trim()

    def json = new groovy.json.JsonSlurper().parseText(response)
    return json.fields.status.name
  }
}
