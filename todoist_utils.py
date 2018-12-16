import configparser


def get_api_token():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['main']['api-key']


def get_project_id(api, project_name):
    project_ids = [project['id'] for project in api.state['projects'] if project['name'] == project_name]

    if len(project_ids) == 0:
        raise LookupError('Project name not found.')

    if len(project_ids) > 1:
        raise LookupError('Multiple projects found: {}'.format(project_ids))

    return project_ids[0]
