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
        'show_output': True

    }, {
        'action': 'delete',
        'method': 'post',
        'params': json.dumps({
            'name': os.environ.get('BANGUMI_2')
        }),
        'show_output': True
    }
]


if __name__ == '__main__':
    for api in api_list:
        r = getattr(requests, api['method'])('http://localhost:8888/api/{}'.format(api['action']),
                                             data=api.get('params', None),
                                             headers={'BGmi-Token': '233'}).json()
        print(api.get('params', None))
        if api['show_output']:
            print(r)
