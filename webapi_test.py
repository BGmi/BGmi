import json
import os

import requests

api_list = [
    {
        'action': 'cal',
        'method': 'get',
        'show_output': False
    }, {
        'action': 'add',
        'method': 'post',
        'params': json.dumps({
            'name': os.environ.get('BANGUMI_2')
        }),

    }, {
        'action': 'delete',
        'method': 'post',
        'params': json.dumps({
            'name': os.environ.get('BANGUMI_2')
        }),
    }, {
        'action': 'mark',
        'method': 'post',
        'params': json.dumps({
            'name': os.environ.get('BANGUMI_2'),
            'episode': 1,
        }),
    }, {
        'action': 'update',
        'method': 'post',
        'params': '{}',
    }, {
        'action': 'status',
        'method': 'post',
        'params': json.dumps({
            'name': os.environ.get('BANGUMI_2'),
            'status': 1,
        }),
    }, {
        'action': 'filter',
        'method': 'post',
        'params': json.dumps({
            'name': os.environ.get('BANGUMI_2'),
            'regex': '.*',
            'subtitle': '',
        }),
    }
]


if __name__ == '__main__':
    exit_code = 0
    for api in api_list:
        r = getattr(requests, api['method'])('http://localhost:8888/api/{}'.format(api['action']),
                                             data=api.get('params', None),
                                             headers={'BGmi-Token': '233'}).json()
        print(api.get('params', None))
        if api.get('show_output', True):
            if r['status'] == 'error':
                exit_code = 1
            print(r)

    exit(exit_code)