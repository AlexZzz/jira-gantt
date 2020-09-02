#!/usr/bin/env python3
import argparse
import sys
import requests
from jira import JIRA
import plotly.express as px
import pandas as pd
from datetime import datetime,timezone,timedelta

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
    histories_list = list()
    for issue in issues:
        issue_full_hist = list()
        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == "status": # "Backlog" "Analyze" "In Progress" "Testing" "Closed"
                    issue_hist = dict()
                    date = datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S.%f%z")
                    issue_hist['Assignee'] = issue.fields.assignee.displayName
                    issue_hist['Task'] = issue.key
                    issue_hist['Status'] = item.toString
                    issue_hist['Start'] = datetime.combine(date.date(), date.time()).isoformat(' ',timespec='minutes')
                    for issue_hist_saved in issue_full_hist:
                        if issue_hist_saved.get('Status') == item.fromString:
                            issue_hist_saved['Finish'] = datetime.combine(date.date(), date.time()).isoformat(' ',timespec='minutes')
                    issue_full_hist.append(issue_hist)
        histories_list += issue_full_hist

    for hist in histories_list:
        if hist.get('Finish') == None:
            hist['Finish'] = datetime.now().isoformat(' ',timespec='minutes') # TODO: Delete timezone everywhere
    print(histories_list)
    df = pd.DataFrame(histories_list)
    print(df)
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Status")
    fig.update_yaxes(autorange="reversed")
    fig.show()
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
