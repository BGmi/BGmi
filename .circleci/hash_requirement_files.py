import hashlib
import os
from os import path
from pathlib import Path

project_root = Path(__file__) / '..' / '..'
requirements_path = [
    'docs/requirements.txt',
    '.pre-commit-config.yaml',
]

for dir, _, files in os.walk(path.join(project_root, 'requirements')):
    for file in files:
        file_path = path.normpath(path.join(dir, file))
        if 'requirements' in file_path:
            requirements_path.append(file_path)

m = hashlib.md5()
for file in sorted(requirements_path):
    with open(file, 'rb') as f:
        content = f.read()
        m.update(content)
print(m.hexdigest())
