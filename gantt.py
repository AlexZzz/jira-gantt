#!/usr/bin/env python3
import argparse
import sys
import requests
from jira import JIRA

def search(jira,label):
    start_at = 0
    maxResults = 50
    total = 100
    issues = list()
    while maxResults <= total-start_at:
        res = jira.search_issues('labels='+label,maxResults=maxResults,startAt=start_at,expand="changelog")
        total = res.total
        start_at += maxResults
        issues += res
    return issues


def parse_users(issues):
    res = {}
    for issue in issues:
        assignee = issue.fields.assignee
        res[assignee.name] = assignee.displayName
    return res

def work(args):
    auth = args.credentials.split(":")
    options = {"server": "https://"+args.jira_url}
    jira = JIRA(options,auth=tuple(auth))
    issues = search(jira,args.label)
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
