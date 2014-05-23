import urllib
import tornado.escape
import tornado.ioloop
import tornado.httpclient
import tornado.gen
import tornado.web
from . import ui_modules

try:
    from urllib.parse import urlencode
except:
    from urllib import urlencode

class BrowserIDHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def on_post_browser_id(self, login_URL):
        assertion = self.get_argument('assertion')
        http_client = tornado.httpclient.AsyncHTTPClient()
        url = 'https://verifier.login.persona.org/verify'
        data = {
            'assertion': assertion,
            'audience': login_URL
        }
        response = yield tornado.gen.Task(
            http_client.fetch,
            url,
            method='POST',
            body=urlencode(data),
        )
        data = tornado.escape.json_decode(response.body)
        if data['status'] == 'okay':
            self.on_browserid_ok(data, email = data['email'])
        else:
            self.on_browserid_error(data, reason = data['reason'])

    def on_browserid_ok(data, email):
        raise NotImplementedError

    def on_browserid_error(data, email):
        raise NotImplementedError

__all__ = [BrowserIDHandler]
