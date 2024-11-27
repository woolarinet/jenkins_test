pipeline {
  agent any

  environment {
    JIRA_REST_API = 'https://sippysoft.atlassian.net/rest/api/3'
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
    if (currentStatus != 'Building') {
      echo "The issue's status is not Building."
      if currentStatus == 'Testing' {
        //TODO: just committed to에 추가
      }
      return
    }

    def transitions = getAvailableTransitions(issueKey)
    def targetTransition = buildResult == 'SUCCESS' ? 'Testing' : 'Re Open'
    def transition = transitions.find { it.name == targetTransition }

    echo "Target Transition: ${targetTransition} / ${transition}"
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
  def res = _getFromJira("/issue/${issueKey}")
  return res.fields.status.name
}

def getAvailableTransitions(issueKey) {
  def res = _getFromJira("/issue/${issueKey}/transitions")
  return res.transitions
}

def _getFromJira(url_postfix) {
  withCredentials([
    string(credentialsId: 'JIRA_API_TOKEN', variable: 'PASSWORD'),
    string(credentialsId: 'JIRA_EMAIL_CREDENTIAL_ID', variable: 'USERNAME')
    ]) {
    echo "prefix: ${url_postfix}"
    def response = sh(
      script: """
      curl --request GET \
          --url '${env.JIRA_REST_API}${url_postfix}' \
          --user '$USERNAME:$PASSWORD' \
          --header 'Accept: application/json'
      """,
      returnStdout: true
    ).trim()

    def json = new groovy.json.JsonSlurper().parseText(response)
    return json
  }
}
