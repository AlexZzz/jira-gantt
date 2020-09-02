#!/usr/bin/env python3
import argparse
import sys
import requests
from jira import JIRA
import plotly.express as px
import pandas as pd
from datetime import datetime,timezone,timedelta

def search(jira,search_filter):
    start_at = 0
    maxResults = 200
    total = 201
    issues = list()
    print("Searching for issues...")
    while maxResults <= total-start_at:
        res = jira.search_issues(search_filter,maxResults=maxResults,startAt=start_at,expand="changelog")
        total = res.total
        start_at += maxResults
        issues += res
        print("Searching for issues... {} got {} left".format(total,total-start_at))
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
    issues = search(jira,args.search_filter)
    histories_list = list()
    for issue in issues:
        issue_full_hist = list()
        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == "status": # "Backlog" "Analyze" "In Progress" "Testing" "Closed"
                    date = datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S.%f%z")
                    if item.toString not in args.exclude_status:
                        issue_hist = dict()
                        issue_hist['Assignee'] = issue.fields.assignee.displayName
                        issue_hist['Task'] = issue.key+" "+issue.fields.summary
                        issue_hist['Status'] = item.toString
                        issue_hist['Start'] = datetime.combine(date.date(), date.time()).isoformat(' ',timespec='minutes')
                    if len(issue_full_hist) and issue_full_hist[-1].get('Status') == item.fromString:
                        issue_full_hist[-1]['Finish'] = datetime.combine(date.date(), date.time()).isoformat(' ',timespec='minutes')
                        print("Setting {} with from={} now={}".format(issue_full_hist[-1]['Task'],item.fromString,item.toString))
                    if item.toString not in args.exclude_status:
                        issue_full_hist.append(issue_hist)
        histories_list += issue_full_hist

    for hist in histories_list:
        if hist.get('Finish') == None:
            hist['Finish'] = datetime.now().isoformat(' ',timespec='minutes')
    df = pd.DataFrame(histories_list)
    df = df.sort_values('Assignee')
    df = df.set_index('Assignee', append=True).swaplevel(0,1)
    print(df)
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Status")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(showgrid=True,gridwidth=1,gridcolor='Black')
    fig.show()
    users = parse_users(issues)
    print(users)

def main():
    parser = argparse.ArgumentParser(description="Plot Gantt by people for tasks by label")
    parser.add_argument('--credentials','-c',type=str,help="Auth credentials in format username:password")
    parser.add_argument('--jira-url','-j',type=str,help="Jira URL")
    parser.add_argument('--exclude-status','-e',type=str,nargs='*',default=["Backlog","Closed"],help="Exclude tasks in this status")
    parser.add_argument('--search-filter','-f',type=str,default="labels=\"CloudAdmins\"",help="Search filter expression")
    args = parser.parse_args()
    work(args)

if __name__=='__main__':
    sys.exit(main())
