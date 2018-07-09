#!/usr/bin/env python

import configparser
import datetime
import logging

import dateutil.parser
from dateutil.tz import tz

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


def is_instantiable(task):
    if task['date_string'] is None or 'every' not in task['date_string'].lower():
        return False
    task_date = dateutil.parser.parse(task['due_date_utc'])
    return task_date.astimezone(tz.tzlocal()).date() == datetime.date.today()


def clone_task(api, task):
    due_date_utc_str = dateutil.parser.parse(task['due_date_utc']).isoformat()
    api.items.add(
        content=task['content'], project_id=task['project_id'],
        due_date_utc=due_date_utc_str, priority=task['priority'],
        indent=task['indent'], collapsed=task['collapsed'],
        labels=task['labels'],
        )


def postpone_task(api, task):
    api.items.update_date_complete(task['id'])


@click.command()
@click.option('--project', 'project_name', required=True)
@click.option('--loglevel', default='warning')
def instantiate(project_name, loglevel):
    api = TodoistAPI(get_api_token())
    api.sync()

    logging.basicConfig(level=getattr(logging, loglevel.upper()))

    project_id = get_project_id(api, project_name)

    tasks = api.projects.get_data(project_id)['items']
    instantiable_tasks = [task for task in tasks if is_instantiable(task)]

    action_count = 0

    for task in instantiable_tasks:
        clone_task(api, task)
        postpone_task(api, task)
        action_count += 2

        # The Todoist API will reject a commit if there are more than 100
        # changes bundled together.  Just to give myself some buffer in case
        # I'm miscounting actions, I commit everytime the action count gets
        # above 80.
        if action_count > 80:
            r = api.commit()
            logging.debug(f"commit = {r!r}")
            action_count = 0

    r = api.commit()
    logging.debug(f"commit = {r!r}")


if __name__ == '__main__':
    instantiate()
