#!/usr/bin/env python

import configparser

import dateutil.parser

import click
from todoist.api import TodoistAPI


def get_api_token():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['main']['api-key']


def get_project_id(api, project_name):
    project_id = None
    for project in api.state['projects']:
        if project['name'] == project_name:
            project_id = project['id']
            break
    if project_id is None:
        raise LookupError('Project name not found.')
    return project_id


@click.command()
@click.option('--project', 'project_name', required=True)
@click.option('--month', required=True)
@click.option('--showtime', is_flag=True)
def export_done(project_name, month, showtime):
    api = TodoistAPI(get_api_token())
    api.sync()

    project_id = get_project_id(api, project_name)

    heading = f'{project_name}: {month}'
    heading_border = len(heading) * '='
    print(heading_border)
    print(heading)
    print(heading_border)
    completed_items = api.items.get_completed(project_id)
    log_dates = {}
    for item in completed_items:
        item_datetime = dateutil.parser.parse(item['due_date_utc']).astimezone()
        item_date = item_datetime.date()
        item_month = item_date.strftime('%Y-%m')
        if month != item_month:
            continue
        if item_date not in log_dates:
            log_dates[item_date] = []
        log_date_section = log_dates[item_date]
        log_record = {
            'timestamp': item_datetime,
            'text': item['content'],
        }
        log_date_section.append(log_record)
    for log_date in sorted(log_dates):
        print('\n-----')
        print(log_date.strftime('%d %a')[0:5])
        print('-----\n')
        day = log_dates[log_date]
        for record in sorted(day, key=lambda x: x['timestamp']):
            if showtime:
                print(f"* [{record['timestamp'].strftime('%H:%M')}] {record['text']}")
            else:
                print('* ' + record['text'])


if __name__ == '__main__':
    export_done()
