# Jira-Gantt

Creates Gantt diagram with tasks and current assignees.

Tasks are colored in accordance to there status at specified date and groupped by current assignee. By default it doesn't show tasks when they were in "Closed" and "Backlog" statuses, see `./gantt.py --help` for more details.

## Bugs

There's a bug with plotly, it may show task wider on Y than it should be. I haven't found a way to fix it yet.

## How To

The simplest way to use is to:
1. Create conda env with `conda create --name <env> --file ./requirements.txt`
2. Run command like `./gantt.py --credentials 'USER:PASSWORD' --jira-url jira.yourcompanyname.org --search-filter '(assignee in (poopa, loopa) or assignee was in (poopa, loopa)) and updated >= -7d'`
