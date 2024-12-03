pipeline {
  agent none

  stages {
    stage('Wake up, builder-on-demand!') {
      steps {
        script {
          echo "Wake up process"
        }
      }
    }
    stage('Acquire Node') {
      stages {
        stage('Build') {
          steps {
            echo 'Building..'
            script {
              if (env.TEST_BUILD_RESULT == "SUCCESS") {
                exit 0
              }
              exit 1
            }
          }
        }
      }
      post {
        success {
          updateJiraIssues('SUCCESS')
        }
        failure {
          updateJiraIssues('FAILURE')
        }
      }
    }
  }
}


def debug(msg) {
  if (env.DEBUG_MODE == 'true') {
    echo "[DEBUG] ${msg}"
  }
}


def getBranchName() {
  String branch_name = scm.branches[0].name.split('/')[1]
  return branch_name
}


def getIssuesFromChanges() {
  def changeLogSets = getPreviousFailedBuilds()
  debug("The number of failed builds before: ${changeLogSets.size()}")
  currentBuild.changeSets.each { cs -> changeLogSets.add(cs) }
  debug("The number of changes should be checked: ${changeLogSets.size()}")

  def issueKeys = []
  debug("Checking commits ...")
  for (int i = 0; i < changeLogSets.size(); i++) {
    def entries = changeLogSets[i].items
    for (int j = 0; j < entries.length; j++) {
      def commitMsg = entries[j].msg
      debug("Commit msg: ${commitMsg}")
      def matcher = commitMsg =~ /(SS-\d+)/
      if (matcher) {
          issueKeys.addAll(matcher.collect { it[1] })
      }
    }
  }
  return issueKeys.unique()
}


def getPreviousFailedBuilds() {
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


def updateJiraIssues(buildResult) {
  def issueKeys = getIssuesFromChanges()
  if (issueKeys.isEmpty()) {
    debug("JIRA Issue Keys not found in commit messages. Skip this step.")
    return
  }
  debug("Target issues: ${issueKeys}")

  def targetVersion = getBranchName()
  debug("Target version: ${targetVersion}")
  withCredentials([
    string(credentialsId: 'JIRA_API_TOKEN', variable: 'PASSWORD'),
    string(credentialsId: 'JIRA_EMAIL_CREDENTIAL_ID', variable: 'USERNAME')
  ]) {
    def debugOption = env.DEBUG_MODE == 'true' ? '-d' : ''
    sh "python3 -m venv venv;source ./venv/bin/activate;python3 ${WORKSPACE}/scripts/transition.py '${issueKeys}' '${currentBuild.number}:${buildResult}' ${targetVersion} $USERNAME $PASSWORD ${debugOption}"
  }
}