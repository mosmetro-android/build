import os
import json
import requests

from .branches import get as get_branches
from .config import config


def download(url: str, dest: str) -> None:
    res = requests.get(url)

    with open(dest, 'wb') as fo:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                fo.write(chunk)


def main():
    print('Fetching branches')
    branches = get_branches()

    for branch in branches.values():
        print(f'Downloading {branch["filename"]}')
        download(branch['url'], f'build/apks/{branch["filename"]}')

        branch['url_orig'] = branch['url']
        branch['url'] = f'{config["base_url"]}/apks/{branch["filename"]}'

    data = dict(config['static'])
    data['branches'] = branches

    with open('build/data.json', 'w') as fo:
        json.dump(data, fo, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
