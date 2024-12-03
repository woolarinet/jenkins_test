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
  echo "${scm}"
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
    sh "source ./venv/bin/activate;python3 ${WORKSPACE}/scripts/jira/jira.py '${issueKeys}' ${buildResult} ${targetVersion} $USERNAME $PASSWORD"
  }
}

def getIssuesFromChanges() {
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
