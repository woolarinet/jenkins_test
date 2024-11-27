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

def getLastBuildStatus() {
  def previousBuild = currentBuild.rawBuild.getPreviousBuild()
  if (previousBuild == null) {
    return 'NONE'
  }
  return previousBuild.getResult().toString()
}

def getNumberOfChanges() {
  int totalChanges = 0
  def changeLogSets = currentBuild.changeSets
  for (int i = 0; i < changeLogSets.size(); i++) {
    def entries = changeLogSets[i].items
    totalChanges += entries.length
  }
  return totalChanges
}

def updateJiraIssues(buildResult) {
  def issueKeys = getTicketNumberFromChanges()
  if (issueKeys.isEmpty()) {
    echo "JIRA Issue Keys not found in commit messages. Skip this step."
    return
  }
  echo "Target issues: ${issueKeys}"

  issueKeys.each { issueKey ->
    echo "Processing JIRA issue: ${issueKey}"

    def currentStatus = getCurrentStatus(issueKey)
    if (currentStatus != 'Building') {
      echo "The issue's status is not building. Skip this step."
      return
    }

    def transitions = getAvailableTransitions(issueKey)
    echo "Available transitions: ${transitions*.name}"

    def targetTransition = buildResult == 'SUCCESS' ? 'Testing' : 'Re Open'
    def transition = transitions.find { it.name == targetTransition }

    if (!transition) {
        echo "'${targetTransition}'is not available for this status."
        return
    }

    def transitionPayload = [
      transition: [
        id: transition.id
      ]
    ]

    if (buildResult == 'SUCCESS') {
      // TODO: committed to 추가
    }

    def response = httpRequest(
        httpMode: 'POST',
        url: "${env.JIRA_BASE_URL}/rest/api/3/issue/${issueKey}/transitions",
        contentType: 'APPLICATION_JSON',
        requestBody: groovy.json.JsonOutput.toJson(transitionPayload),
        authentication: env.JIRA_CREDENTIALS_ID,
        validResponseCodes: '204'
    )

    if (response.status == 204) {
      echo "'${issueKey}' has been moved to '${targetTransition}'."
    } else {
      echo "'${issueKey}' has been failed to move to '${targetTransition}'."
      echo "response status: ${response.status}"
      echo "response content: ${response.content}"
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