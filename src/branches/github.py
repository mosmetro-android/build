import requests
from ..config import config


class GitHubBranch(dict):
    def __init__(self, name, json):
        version = int(json['tag_name'])

        self['name'] = name
        self['version'] = version
        self['build'] = 0
        self['by_build'] = False
        self['url'] = json['assets'][0]['browser_download_url']
        self['message'] = f'{json["name"]}:\n{json["body"]}'
        self['filename'] = f'MosMetro-{name}-v{version}.apk'
        self['stable'] = name in config['stable_branches']


class GitHub(dict):
    def __init__(self, user, repo):
        url = f'https://api.github.com/repos/{user}/{repo}/releases'

        headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0)'}
        json = requests.get(url, headers=headers).json()

        # Looking for 'beta' (latest) and 'play' (latest stable)
        beta = json[0]
        play = [r for r in json if not r['prerelease']][0]

        if config['github']['beta']:
            self['beta'] = GitHubBranch('beta', beta)

        self['play'] = GitHubBranch('play', play)


if __name__ == '__main__':
    print(GitHub(config['github']['user'], config['github']['repo']))
