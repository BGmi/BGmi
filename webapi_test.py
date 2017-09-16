import json
import os

import requests

api_list = [
    {
        'action': 'cal',
        'method': 'get',
    }, {
        'action': 'add',
        'method': 'post',
        'params': json.dumps({
            'name': [os.environ.get('BANGUMI_3'), ]
        })
    }, {
        'action': 'delete',
        'method': 'post',
        'params': json.dumps({
            'name': [os.environ.get('BANGUMI_3'), ]
        })
    }
]

for api in api_list:
    print(api.get('params', None))
    r = getattr(requests, api['method'])('http://localhost:8888/api/{}'.format(api['action']),
                                         data=api.get('params', None)).json()
    print(r)
