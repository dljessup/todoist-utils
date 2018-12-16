#!/usr/bin/env python

import logging

import click
from todoist.api import TodoistAPI
import yaml

from todoist_utils import get_api_token, get_project_id


# priority should always be 4
# indent should always be 1
# author should always be David (41563)
# responsible should always be empty
# date_lang should always be en
# timezone should always be America/New_York


@click.command()
@click.option('--project', 'project_name', required=True)
@click.option('--source', 'source_filename', required=True)
@click.option('--dry-run/--wet-run', 'dry_run', default=False)
@click.option('--loglevel', type=click.Choice(['debug', 'info', 'warning', 'error', 'critical']), default='warning')
def sync(project_name, source_filename, dry_run, loglevel):
    logging.basicConfig(level=getattr(logging, loglevel.upper()))

    api = TodoistAPI(get_api_token())
    api.sync()

    project_id = get_project_id(api, project_name)

    project_items = {}
    for item in api.state['items']:
        if item['project_id'] != project_id:
            continue
        try:
            in_history = item['in_history']
        except KeyError:
            continue
        if in_history == 1:
            continue
        project_items[item['content']] = item

    logging.debug('project_items = {!r}'.format(project_items))

    project_notes = {}
    for note in api.state['notes']:
        if note['project_id'] != project_id or note['is_archived'] == 1:
            continue
        if note['item_id'] in project_notes:
            project_notes[note['item_id']].append(note)
        else:
            project_notes[note['item_id']] = [note]
    logging.debug('project_notes = {!r}'.format(project_notes))

    labels = {label['name']: label['id'] for label in api.state['labels']}
    logging.debug('labels = {}'.format(labels))

    source_model = yaml.load(open(source_filename, 'r'))

    logging.debug('source_model = {!r}'.format(source_model))

    api_model = []
    i = 0
    for source_item in source_model:
        i += 1
        if source_item['content'] in project_items:
            api_item = project_items[source_item['content']]
            del project_items[source_item['content']]
        elif source_item.get('prev_content') in project_items:
            api_item = project_items[source_item['prev_content']]
            del project_items[source_item['prev_content']]
            logging.debug('prev_content → content: {} → {}'.format(source_item['prev_content'], source_item['content']))
            if not dry_run:
                api_item.update(content=source_item['content'])
        else:
            logging.debug('add: {}'.format(source_item['content']))
            if dry_run:
                api_item = source_item['content']
            else:
                api_item = api.items.add(content=source_item['content'], project_id=project_id)

        source_label_ids = [labels[name] for name in source_item['labels']]

        logging.debug('update: {}: {}: {}: {}'.format(api_item, source_item['date'], i, source_label_ids))
        if not dry_run:
            api_item.update(date_string=source_item['date'], item_order=i, labels=source_label_ids)

        source_notes = source_item.get('notes', [])
        api_notes = project_notes.get(api_item['id'], [])
        logging.debug('source notes = {}'.format(source_notes))
        logging.debug('api notes = {}'.format(api_notes))
        for i in range(0, max(len(source_notes), len(api_notes))):
            if len(source_notes) <= i:
                logging.debug('delete note: {}'.format(api_notes[i]))
                if not dry_run:
                    api_notes[i].delete()
            elif len(api_notes) <= i:
                logging.debug('add note: {}'.format(source_notes[i]))
                if not dry_run:
                    api.notes.add(api_item['id'], source_notes[i])
            else:
                if api_notes[i]['content'].strip() != source_notes[i].strip():
                    logging.debug('update note: {} → {}'.format(api_notes[i]['content'], source_notes[i]))
                    if not dry_run:
                        api_notes[i].update(content=source_notes[i])

    for api_item in project_items.values():
        logging.debug('delete: {}'.format(api_item))
        if not dry_run:
            api_item.delete()
    if not dry_run:
        api.commit()


if __name__ == '__main__':
    sync()
