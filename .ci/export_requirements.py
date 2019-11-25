import argparse
import os

import toml


def _poetry_lock_to_requirements_txt(start_dir, options):
    with open(f'{start_dir}/poetry.lock') as f:
        lock = toml.load(f)
    hashes = lock['metadata']['hashes']
    s = ''
    for package in lock['package']:
        if not options.all and (package.get('category') != 'main' or package.get('optional')):
            continue

        name = package['name']
        version = package['version']
        marker = f'; {package["marker"]}' if 'marker' in package else ''

        hash_args = ' '.join([f'--hash=sha256:{x}' for x in hashes.get(name, [])])

        s += f'{name}=={version} {marker} {hash_args}\n'

    with open(f'{start_dir}/requirements.txt', 'w', encoding='utf-8') as f:
        f.write(s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', default=False, action='store_true')
    opt = parser.parse_args()
    workdir = os.getcwd()
    _poetry_lock_to_requirements_txt(workdir, opt)
