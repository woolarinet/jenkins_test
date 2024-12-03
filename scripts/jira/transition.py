#!/usr/local/bin/python

import re
import json
import argparse
import requests

from requests.auth import HTTPBasicAuth


BASE_URL = "https://sippysoft.atlassian.net/rest/api/3"


def debug(debug_mode, msg):
    if debug_mode:
        print(msg)


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

    for committed_version in committed_versions: # existing committed_to versions
        targets.append({"id": committed_version["id"]})

    if not is_succeed:
        return params

    # current version
    targets += [{"id": v["id"]} for v in all_versions if v["value"].strip() == version.strip()]
    return params


def _get_params(auth, is_succeed, committed_versions, version, build_number, transition=None):
    if not is_succeed and transition: # when it's moved to Reopened
        return {"transition": {"id": transition["id"]}}

    params = {
        "update": {
            "comment": [{
                  "add": {
                      "body": {
                        "content": [{
                            "content": [{
                                "text": f"The buildupdate(#{build_number}) of {version} has " + ("succeeded" if is_succeed else "failed"),
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


def request_to_jira(url, auth, method="GET", headers={"Accept": "application/json"}, data=None):
    """
    Sends an HTTP request to a JIRA API endpoint.

    Parameters:
        url (str): The API endpoint URL.
        auth (tuple): A tuple containing (username, password) or token.
        method (str): The HTTP method to use ("GET", "POST", "PUT", etc.).
        headers (dict): The request headers.
        data (dict or str): The data to send in the request body).

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
        )

        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json() if method == "GET" else response.text # Automatically parse the response JSON
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def issue_trasition(auth, i_issue, is_succeed, version, build_number, debug_mode):
    fields = _get_fields(auth, i_issue)
    current_status = fields["status"]["name"]
    committed_versions = fields.get("customfield_11400") or []

    if current_status != 'Building':
        debug(debug_mode, f"The issue's status is not Building: {current_status}")
        if current_status != 'Testing' or not is_succeed:
            return

        # If the current version is already added to 'committed_to', it just ends the process.
        if next((v for v in committed_versions if v["value"].strip() == version.strip()), None):
            debug(debug_mode, f"Current version has been already added into 'committed_to'. Nothing to need to process.")
            return

        # Add committed_to version only.
        params = _get_params(auth, is_succeed, committed_versions, version, build_number)
        return request_to_jira(f"/issue/{i_issue}", auth, "PUT", data=json.dumps(params))

    transitions = _get_available_transitions(auth, i_issue)
    target_transition = "Testing" if is_succeed else "Re Open"
    transition = next((t for t in transitions if t["name"] == target_transition), None)
    params = _get_params(auth, is_succeed, committed_versions, version, build_number, transition)
    request_to_jira(f"/issue/{i_issue}/transitions", auth, "POST", data=json.dumps(params))

    if not is_succeed: # leave a comment when it's failed after transition
        request_to_jira(
            f"/issue/{i_issue}", auth, "PUT", data=json.dumps(
                _get_params(auth, is_succeed, committed_versions, version, build_number)
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jira Auto Transition Script")
    parser.add_argument('i_issues', help='Comma-separated list of Jira issue keys (e.g., "[SS-123,SS-456]")')
    parser.add_argument('result', help='Build result in the format "BUILD_NUMBER:RESULT" (e.g., "123:SUCCESS")')
    parser.add_argument('version', help='Target version for transition (e.g., "master", "freightswitch", ...)')
    parser.add_argument('userid', help='Jira user email')
    parser.add_argument('password', help='Jira api token')

    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()
    build_number, build_result = args.result.split(":")
    is_succeed = build_result.upper() == "SUCCESS"

    auth = HTTPBasicAuth(args.userid, args.password)
    i_issues = re.sub(r'[\[\]\s]', '', args.i_issues).split(',')

    debug(args.debug, "[DEBUG] Arguments ===============================")
    debug(args.debug, f"[DEBUG] Issues: {i_issues}")
    debug(args.debug, f"[DEBUG] Build Number: {build_number}")
    debug(args.debug, f"[DEBUG] Build Result: {build_result}")
    debug(args.debug, f"[DEBUG] Version: {args.version}")
    debug(args.debug, f"[DEBUG] UserID: {args.userid}\n\n")

    for i_issue in i_issues:
        issue_trasition(auth, i_issue, is_succeed, args.version, build_number, args.debug)
