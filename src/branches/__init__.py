from .jenkins import Jenkins
from .github import GitHub

from ..config import config


def get():
    branches = dict()
    branches.update(Jenkins(config['jenkins']['url'],
                            config['jenkins']['project']))

    if branches.get('play'):  # Branch 'play' must be loaded from GitHub
        play_description = branches['play'].get('description')
        del branches['play']
    else:
        play_description = 'Описание отсутствует'

    if config['github']['enabled']:
        branches.update(GitHub(config['github']['user'],
                               config['github']['repo']))

        if 'play' in branches:
            branches['play']['description'] = play_description

    return branches


if __name__ == '__main__':
    import json
    print(json.dumps(get(), ensure_ascii=False, indent=2))
