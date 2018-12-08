import configparser


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
