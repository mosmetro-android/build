import requests
from ..config import config


class JenkinsBranch(dict):
    def _change_set_recursive(self, number):
        url = f'{self.base_url}/{number}/api/json'
        build = requests.get(url).json()
        changes = self._change_set(build)

        if len(changes) == 0:
            return self._change_set_recursive(build['number'] - 1)

        return changes

    def _change_set(self, build):
        changes = []

        if 'changeSet' in build:
            changes += build['changeSet']['items']
        elif 'changeSets' in build:
            for cs in build['changeSets']:
                changes += cs['items']

        if len(changes) == 0:
            changes = self._change_set_recursive(build['number'] - 1)

        return changes

    def __init__(self, project, name):
        self.base_url = f'{project.base_url}/job/{name}'
        api_url = f'{self.base_url}/api/json'

        branch = requests.get(api_url).json()
        build_api_url = branch['lastSuccessfulBuild']['url'].rstrip('/')
        build = requests.get(f'{build_api_url}/api/json').json()

        artifacts = [x['relativePath'] for x in build['artifacts']]
        artifact = [x for x in artifacts if 'signed' in x][0]

        version = build['number']

        self['name'] = name
        self['description'] = branch['description']
        self['version'] = 0
        self['build'] = version
        self['by_build'] = True
        self['url'] = f'{build["url"]}/artifact/{artifact}'
        self['filename'] = f'MosMetro-{name}-b{version}.apk'
        self['stable'] = name in config['stable_branches']
        self.buildable = branch['buildable']

        message = f'Сборка {name}-#{version}:\n'

        try:
            changes = self._change_set(build)

            if len(changes) == 0:
                raise Exception('Empty change set')

            for change in changes:
                message += f'\n* {change["msg"]}'
        except Exception:
            message += '¯\_(ツ)_/¯'

        self['message'] = message


class Jenkins(dict):
    def __init__(self, url, project):
        self.base_url = f'{url}/job/{project}'
        api_url = f'{self.base_url}/api/json'

        json = requests.get(api_url).json()

        branches = [branch['name']
                    for branch in json['jobs']
                    if branch['color'] != 'disabled']

        for branch in branches:
            t = JenkinsBranch(self, branch)

            if not t.buildable:
                continue

            if t['name'][0] == '_' and not config['jenkins']['private_branches']:
                continue

            self[branch] = t


if __name__ == '__main__':
    print(Jenkins(config['jenkins']['url'], config['jenkins']['project']))
