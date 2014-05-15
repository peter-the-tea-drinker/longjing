from longjing.ui_modules import BrowserID_form,KOTemplate
import tornado.web
import re

class Stat(tornado.web.UIModule):
    def render(self,stat):
        return self.render_string('stat.html',**stat)
