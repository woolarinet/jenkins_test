import re
import sys
import json
import requests

from requests.auth import HTTPBasicAuth


BASE_URL = "https://sippysoft.atlassian.net/rest/api/3"


def _get_fields(auth, i_issue):
    res = request_to_jira(f"/issue/{i_issue}", auth)
    return res["fields"]


def _get_available_versions(auth):
    res = request_to_jira("/issue/createmeta?projectKeys=SS&expand=projects.issuetypes.fields", auth)
    return res["projects"][0]["issuetypes"][0]["fields"]["customfield_11400"]["allowedValues"]


def _get_available_transitions(auth, i_issue):
    res = request_to_jira(f"/issue/{i_issue}/transitions", auth)
    return res["transitions"]


def _get_committed_to_params(auth, is_succeed, committed_versions, version):
    all_versions = _get_available_versions(auth)
    targets = []
    params = {"fields": {"customfield_11400": targets}}

    for committed_version in committed_versions:
        targets.append({"id": committed_version["id"]})

    if not is_succeed:
        return params

    targets += [{"id": v["id"]} for v in all_versions if v["value"].strip() == version.strip()]
    return params


def _get_params(auth, is_succeed, committed_versions, version, transition=None):
    if not is_succeed and transition:
        return {"transition": {"id": transition["id"]}}

    params = {
        "update": {
            "comment": [{
                  "add": {
                      "body": {
                        "content": [{
                            "content": [{
                                "text": f"buildupdate of {version} has been " + ("succeed" if is_succeed else "failed"),
                                "type": "text"
                            }],
                            "type": "paragraph"
                        }],
                        "type": "doc",
                        "version": 1,
                      }
                  }
            }]
        }
    }
    if transition:
        params.update({"transition": {"id": transition["id"]}})

    params.update(_get_committed_to_params(auth, is_succeed, committed_versions, version))
    return params


def request_to_jira(url, auth, method="GET", headers={"Accept": "application/json"}, data=None, json=None):
    """
    Sends an HTTP request to a JIRA API endpoint.

    Parameters:
        url (str): The API endpoint URL.
        auth (tuple): A tuple containing (username, password) or token.
        method (str): The HTTP method to use ("GET", "POST", "PUT", etc.).
        headers (dict): The request headers.
        data (dict or str): The data to send in the request body (optional, for "application/x-www-form-urlencoded" or similar).
        json (dict): The JSON data to send in the request body (optional).

    Returns:
        dict: The JSON response parsed into a Python dictionary.
    """
    try:
        if method != "GET":
            headers.update({"Content-Type": "application/json"})

        response = requests.request(
            method=method,
            url=BASE_URL+url,
            headers=headers,
            auth=auth,
            data=data,
            json=json
        )

        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json() if method == "GET" else response.text # Automatically parse the response JSON
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def issue_trasition(auth, i_issue, is_succeed, version):
    fields = _get_fields(auth, i_issue)
    current_status = fields["status"]["name"]
    committed_versions = fields.get("customfield_11400", [])

    if current_status != 'Building':
        print(f"The issue's status is not Building: {current_status}")
        if current_status != 'Testing' or not is_succeed:
            return

        params = _get_params(auth, is_succeed, committed_versions, version)
        return request_to_jira(f"/issue/{i_issue}", auth, "PUT", data=json.dumps(params))

    transitions = _get_available_transitions(auth, i_issue)
    target_transition = "Testing" if is_succeed else "Re Open"
    transition = next((t for t in transitions if t["name"] == target_transition), None)
    params = _get_params(auth, is_succeed, committed_versions, version, transition)
    request_to_jira(f"/issue/{i_issue}/transitions", auth, "POST", data=json.dumps(params))

    if not is_succeed: # leave a comment
        request_to_jira(
            f"/issue/{i_issue}", auth, "PUT", data=json.dumps(
                _get_params(auth, is_succeed, committed_versions, version)
            )
        )


if __name__ == "__main__":
  i_issues, result, version = sys.argv[1:4]
  userid, password = sys.argv[4:]

  auth = HTTPBasicAuth(userid, password)
  i_issues = re.sub(r'[\[\]]', '', i_issues).split(',')
  is_succeed = True if result == "SUCCESS" else False

  for i_issue in i_issues:
    issue_trasition(auth, i_issue, is_succeed, version)
