#!/usr/bin/env python3
import argparse
import sys
import requests
from jira import JIRA
import plotly.express as px
import pandas as pd
from datetime import datetime,timezone,timedelta

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
import plotly.colors as pc

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
        issue_plan = dict()
        if issue.fields.customfield_10253 and issue.fields.customfield_10254:
            plan_start = datetime.strptime(issue.fields.customfield_10253, "%Y-%m-%d")
            plan_end = datetime.strptime(issue.fields.customfield_10254, "%Y-%m-%d")
            issue_plan['Assignee'] = issue.fields.assignee.displayName
            issue_plan['Username'] = issue.fields.assignee.name
            issue_plan['Task'] = issue.key+" "+issue.fields.summary
            issue_plan['Status'] = 'Planned'
            issue_plan['Start'] = pd.to_datetime(datetime.combine(plan_start.date(), plan_start.time()).isoformat(' ',timespec='minutes'))
            issue_plan['Finish'] = pd.to_datetime(datetime.combine(plan_end.date(), plan_end.time()).isoformat(' ',timespec='minutes'))
            print(issue_plan)
            issue_full_hist.append(issue_plan)

        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == "status": # "Backlog" "Analyze" "In Progress" "Testing" "Closed"
                    date = datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S.%f%z")
                    if len(issue_full_hist) and issue_full_hist[-1].get('Status') == item.fromString:
                        issue_full_hist[-1]['Finish'] = pd.to_datetime(datetime.combine(date.date(), date.time()).isoformat(' ',timespec='minutes'))
                        print("Setting {} with from={} now={}".format(issue_full_hist[-1]['Task'],item.fromString,item.toString))
                    if item.toString not in args.exclude_status:
                        issue_hist = dict()
                        issue_hist['Username'] = issue.fields.assignee.name
                        issue_hist['Assignee'] = issue.fields.assignee.displayName
                        issue_hist['Task'] = issue.key+" "+issue.fields.summary
                        issue_hist['Status'] = item.toString
                        issue_hist['Start'] = pd.to_datetime(datetime.combine(date.date(), date.time()).isoformat(' ',timespec='minutes'))
                        issue_full_hist.append(issue_hist)
        histories_list += issue_full_hist

    for hist in histories_list:
        if hist.get('Finish') == None:
            hist['Finish'] = pd.to_datetime(datetime.now().isoformat(' ',timespec='minutes'))

    df = pd.DataFrame(histories_list)
    df = df.sort_values('Assignee')

    if args.search_external_issues:
        for user in df['Username'].unique():
            external_filter = 'issueFunction in commented("by {}")'.format(user)
            if args.external_search_filter:
                external_filter += " and "+args.external_search_filter
            external_issues = search(jira,external_filter)

    fig = go.Figure()
    # Here is a hack for https://github.com/plotly/plotly.js/issues/2391
    # plotly.js converts date to ms since epoch and adds to the base
    # So we count diff and pass it in 'x', it then is added to base
    df['Diff'] = pd.to_datetime((df['Finish'].astype(int) - df['Start'].astype(int)))
    print(df)
    colors = pc.sequential.haline
    for i, status in enumerate(df['Status'].unique()):
        df_plot = df[df['Status'] == status]
        bar_color = colors[i]
        marker_line_width = 0
        opacity = 1
        marker_line_color = None
        width = None

        if status == 'Planned':
            opacity = 0.2
            marker_line_width = 2
            marker_line_color = 'Black'
            width = 1

        fig.add_trace(go.Bar(
                base=df_plot['Start'],
                x=df_plot['Diff'],
                y=[df_plot['Assignee'],
                    df_plot['Task']
                ],
                orientation='h',
                marker_color=bar_color,
                opacity=opacity,
                name=status,
                marker_line_width=marker_line_width,
                marker_line_color=marker_line_color,
                width=width,
                hovertemplate=
                    '<i>Since: %{base}</i><br>'+
                    'Until: %{x}'
            ))
    today = datetime.today()
    tomorrow = datetime.today() + timedelta(days=1)
    this_month = today.replace(day=1)
    next_month = (datetime.today() + timedelta(days=32)).replace(day=1)

    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(showgrid=True,gridwidth=1,gridcolor='Black')
    fig.update_layout(barmode='stack',
            hovermode='y',
            shapes=[
                dict(
                    type="rect",
                    x0=today.date(),
                    x1=tomorrow.date(),
                    opacity=0.5,
                    fillcolor="LightSalmon",
                    layer="below",
                    line_width=0,
                    y0=0,
                    y1=1,
                    yref="paper",
                    ),
                dict(
                    type="rect",
                    x0=this_month.date(),
                    x1=next_month.date(),
                    opacity=0.3,
                    fillcolor="LightYellow",
                    layer="below",
                    line_width=1,
                    y0=0,
                    y1=1,
                    yref="paper",
                    ),
                ]
            )
    fig.show()
    users = parse_users(issues)
    print(users)

def main():
    parser = argparse.ArgumentParser(description="Plot Gantt by people for tasks by label")
    parser.add_argument('--credentials','-c',type=str,help="Auth credentials in format username:password")
    parser.add_argument('--jira-url','-j',type=str,help="Jira URL")
    parser.add_argument('--exclude-status','-e',type=str,nargs='*',default=["Backlog","Closed"],help="Exclude tasks in this status")
    parser.add_argument('--search-filter','-f',type=str,default="labels=\"CloudAdmins\"",help="Search filter expression")
    parser.add_argument('--search-external-issues','-v',action='store_true',help="Search all issues for commented by users we are dealing with")
    parser.add_argument('--external-search-filter','-s',type=str,default="updatedDate >= -1w",help="Extra filter for external search expression")
    args = parser.parse_args()
    work(args)

if __name__=='__main__':
    sys.exit(main())
