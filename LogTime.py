from jira import JIRA
from datetime import datetime
import datetime as dt
import dateutil.parser
from dateutil.relativedelta import relativedelta
import argparse
import sys
import getpass

parser = argparse.ArgumentParser(description='Jira time log.')
parser.add_argument('--startdate', type=datetime, default=datetime.today().replace(day=1).date(), help= 'Date in format yyyy-mm-dd')
parser.add_argument('--server', type= str, default='https://koresystemsgroup.atlassian.net', help='Enter server address')
parser.add_argument('--displayname', type= str, help='Enter Jira full display name', nargs='+', default='', required=True)
parser.add_argument('--projectkey', type= str, default='', help='Enter comma delimited project key')
parser.add_argument('--timeinterpolation', type= bool, default=False, help='When set to True, it will fill all time log until today.')

def ListAllIssues(project, search_query):
    block_size = 25
    block_num = 0
    allissues=[]
    while True:
        start_idx = block_num*block_size
        if(project == 'INT'):
            str = "\'INT\'"
            issues = jira.search_issues(search_query, startAt=start_idx, maxResults=block_size, expand='changelog')
        else:
            issues = jira.search_issues(search_query, startAt=start_idx, maxResults=block_size, expand='changelog')
        if len(issues) == 0:
            break
        block_num += 1
        for issue in issues:
            allissues.append(issue)
    return allissues

def LogTime(projects):
    tickets_assigned = []
    for proj in projects:
        proj= proj.upper()
        print(f"Searching tickets in project {proj}...")
        first_day = startDate
        prev_month = first_day - relativedelta(months=1)
        if(str(proj) == 'INT'):
            proj = "\'INT\'"
        relevant_issues = ListAllIssues(str(proj),f"project= {str(proj)} and updated >= {str(prev_month)}")


        for ticket in relevant_issues:
            if (ticket.fields.resolutiondate != None and str(ticket.fields.status) == 'Done'):
                for history in ticket.changelog.histories:
                    for item in history.items:
                        if item.field == 'assignee' and str(item.fromString) == displayName \
                                and dateutil.parser.parse(ticket.fields.resolutiondate).date() >= first_day:
                            tickets_assigned.append({ticket.key: str(dateutil.parser.parse(history.created).date())})
                            break

            if str(ticket.fields.status) != 'Done':
                if (str(ticket.fields.assignee) == displayName):
                    updated_date = dateutil.parser.parse(ticket.fields.updated).date()
                    if (updated_date < first_day):
                        updated_date = first_day
                    tickets_assigned.append({ticket.key: str(updated_date)})


    return tickets_assigned


if __name__ == "__main__":
    args = parser.parse_args()
    if args.displayname == '':
        print("Display name missing.")
        parser.print_usage()
        sys.exit(1)
    user = input("Username:")
    password = getpass.getpass("Password:")

    displayName = ' '.join(args.displayname)
    startDate = args.startdate
    server = args.server
    projectNames = [proj for proj in args.projectkey.split(',') if proj != '']

    server = {'server': server}
    jira = JIRA(options=server, basic_auth=(user, password))

    print("Logging time...")
    projects = []
    if len(projectNames) < 1:
        jira_projects = jira.projects()
        for proj in jira_projects:
            projects.append(proj.key)
    else:
        projects = projectNames
    tickets_assigned = LogTime(projects)

    if(len(tickets_assigned) < 1):
        print("No ticket found.")
        sys.exit(1)
    print('Tickets logged:')
    for item in tickets_assigned:
        for k, v in item.items():
            ticket = jira.issue(k)
            print(f'{ticket.key}: {ticket.fields.summary}')
            try:
                jira.add_worklog(ticket, timeSpent='8h', comment=ticket.fields.summary,
                             started=dateutil.parser.parse(v).date() + dt.timedelta(days=1))
            except:
                print("You do not have the permission to associate a worklog to this issue.")

    print("Done logging time.")