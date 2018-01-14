#!/usr/bin/env python

import configparser

import dateutil.parser

import click
from todoist.api import TodoistAPI


def get_api_token():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['main']['api-key']


def get_completed_items(api, project_id, month):
    # The naïve approach for the following code would be to simply return
    # api.items.get_completed(project_id).
    # However, the Todoist API only returns the last 30 completed records and doesn't provide a
    # documented direct mechanism to page for more records.
    # We work around this by using the activity log to find the IDs of items that have been
    # completed at least once.
    # We pass in the month so that we can limit the amount of activity logs that we have to
    # page through.
    # so

    activity = []
    activity_buffer = None
    offset = 0
    limit = 100
    while activity_buffer is None or len(activity_buffer) > 0:
        activity_buffer = api.activity.get(
            object_type='item', event_type='completed', parent_project_id=project_id,
            limit=limit, since=(month + '-01T00:00'), offset=offset)
        activity += activity_buffer
        offset += limit

    # Because we're using the activity logs, we may pick up duplicate item IDs (if an item is
    # recurring, or if an item was completed in error, uncompleted, and then recompleted
    # later).
    completed_item_ids = set([event['object_id'] for event in activity])
    completed_items = []
    for item_id in completed_item_ids:
        item = api.items.get_by_id(item_id)
        if type(item) == dict:
            item = item['item']

        # Because we're using the activity logs, we may pick up an item that is still active,
        # if the item is recurring or if the item was uncompleted after being completed.
        if item['in_history'] == 1:
            completed_items.append(item)
    return completed_items


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

    completed_items = get_completed_items(api, project_id, month)

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
