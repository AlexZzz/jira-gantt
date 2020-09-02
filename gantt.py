#!/usr/bin/env python3
import argparse
import sys
import requests
from jira import JIRA


def search(url,auth):
    start_at = 0
    r = requests.get(url+"&startAt="+str(start_at),auth=auth)
    res = r.json()
    issues = res.get("issues")
    while res.get("maxResults") < res.get("total")-start_at:
        r = requests.get(url+"&startAt="+str(res.get("maxResults")+start_at))
        issues += res.get("issues")
    return issues

def parse_users(issues):
    res = {}
    for issue in issues:
        assignee = issue.get("fields").get("assignee")
        res[assignee.get("name")] = assignee.get("displayName")
    return res

def work(args):
    auth = args.credentials.split(":")
    options = {"server": "https://"+args.jira_url}
    jira = JIRA(options)
    api_url = "https://"+args.jira_url+"/rest/api/latest/"
    search_issues_url = api_url+"search?jql=labels=\""+args.label+"\""
    issues = search(search_issues_url,tuple(auth))
    users = parse_users(issues)
    print(users)

def main():
    parser = argparse.ArgumentParser(description="Plot Gantt by people for tasks by label")
    parser.add_argument('--label','-l',type=str,help="Label name")
    parser.add_argument('--credentials','-c',type=str,help="Auth credentials in format username:password")
    parser.add_argument('--jira-url','-j',type=str,help="Jira URL")
    args = parser.parse_args()
    work(args)

if __name__=='__main__':
    sys.exit(main())
