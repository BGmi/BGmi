import json

from tornado.web import RequestHandler

from bgmi.controllers import *


class dict2obj(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [dict2obj(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, dict2obj(b) if isinstance(b, dict) else b)

    def __getattr__(self, item):
        return None


class ApiHandle(RequestHandler):
    def get(self, action, *args, **kwargs):
        if action == ACTION_CAL:
            data = {'action': action, 'force_update': False}
            r = controllers(dict2obj(data))
            self.finish(r)
        elif action == 'update':
            data = {'action': ACTION_CAL, 'force_update': True}
            r = controllers(dict2obj(data))
            self.finish(r)

        # self.set_header("Content-Type", "application/json")
        # self.write({'support action': ACTIONS})

    def post(self, action, *args, **kwargs):
        try:
            data = json.loads(self.request.body.decode('utf-8'))
        except json.JSONEncoder:
            self.write_error(502)
            return
        print(type(data))
        if action == ACTION_DELETE:
            data['action'] = action
            ret = dict2obj(data)
            self.write(controllers(ret))
            return
        elif action == ACTION_ADD:
            data['action'] = action
            ret = dict2obj(data)
            self.write(controllers(ret))
            return
        elif action == ACTION_SEARCH:
            self.finish({'status': 'success', 'data': search_without_filter(data['keyword'])})
            pass
        elif action == ACTION_CONFIG:
            pass
        elif action == 'download':
            r = download_prepare(data['data'])
            self.write(r)
        elif action == ACTION_FETCH:
            data['action'] = action
            ret = dict2obj(data)
            controllers(ret)
    def options(self, *args, **kwargs):
        self.write('')
