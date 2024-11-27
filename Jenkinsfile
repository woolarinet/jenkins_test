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

    def fields = getFields(issueKey)
    def currentStatus = fields.status.name
    def committed_to = fields.customfield_11400
    def committedVersion = getCommittedVersion(committed_to, targetVersion)

    if (currentStatus != 'Building') {
      echo "The issue's status is not Building: ${currentStatus}"
      if (currentStatus == 'Testing') {
        if (buildResult == 'SUCCESS' && !committedVersion) {
            //TODO: just committed to에 추가
            // changeStatus()
            return
        }
      }
      return
    }

    echo "committed_to: ${committed_to}"
    echo "committedVersion: ${committedVersion}"

    def transitions = getAvailableTransitions(issueKey)
    echo "transitions: ${transitions}"
    def targetTransition = buildResult == 'SUCCESS' ? 'Testing' : 'Re Open'
    // def transition = transitions.find { it.name == targetTransition }

    // echo "Target Transition: ${targetTransition} / ${transition}"
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

def getFields(issueKey) {
  def res = _getFromJira("/issue/${issueKey}")
  return res.fields
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
    echo "postfix: ${url_postfix}"
    echo "USERNAME / PASSWORD: $USERNAME / $PASSWORD"
    def response = sh(
      script: """
      curl --request GET \
          --url '${env.JIRA_REST_API}${url_postfix}' \
          --user '$USERNAME:$PASSWORD' \
          --header 'Accept: application/json'
      """,
      returnStdout: true
    ).trim()

    def json = readJSON text: response
    return json
  }
}

def getCommittedVersion(committed, targetVersion) {
  echo "committed: ${committed}"
  if (committed.isEmpty()) {
    return
  }

  for (version in committed) {
    if (version.value == targetVersion) {
      return version
    }
  }
}

def getTargetTransitionId() {

}