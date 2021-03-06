import tornado.web
import re
class BrowserID_form(tornado.web.UIModule):
    def render(self):
        xsrf_html_form = self.handler.xsrf_form_html()
        return '''<form id="login-form" method="POST" action="status">
        %s
        <input id="assertion-field" type="hidden" name="assertion" value="" />
        </form>'''%xsrf_html_form

    def embedded_javascript(self):
           return '''
           function loginBrowserID() {
              navigator.id.get(function(assertion) {
                  if (assertion) {
                      var assertion_field = document.getElementById("assertion-field");
                      assertion_field.value = assertion;
                      var login_form = document.getElementById("login-form");
                      login_form.submit();
                  }
              });
           }'''

    def javascript_files(self):
        return ('https://login.persona.org/include.js',)

class JSTemplate(tornado.web.UIModule):
    def _get_template_source(self,template_name):
        from tornado.web import RequestHandler
        import os
        # see UILModule's source
        template_path = self.handler.get_template_path()
        if not template_path:
            frame = sys._getframe(0)
            web_file = frame.f_code.co_filename
            while frame.f_code.co_filename == web_file:
                frame = frame.f_back
            template_path = os.path.dirname(frame.f_code.co_filename)
        with RequestHandler._template_loader_lock:
            if template_path not in RequestHandler._template_loaders:
                loader = self.create_template_loader(template_path)
                RequestHandler._template_loaders[template_path] = loader
            else:
                loader = RequestHandler._template_loaders[template_path]

        path = os.path.join(loader.root, template_name)
        return open(path, "rb").read().decode('utf8')

class KOTemplate(JSTemplate):
    '''Generates the template, with python code stripped out.
    '''
    _tornado_template_code = re.compile('({%.*?%})|{#(.*?)#}|{{(.*?)}}')
    _CACHE = {}
    def render(self,template_name):
        try:
            return _CACHE[template_name]
        except:
            #source = self._interp_block.sub('<%=\\1%>',source)
            #source = self._comment.sub('\\1',source)
            source = self._get_template_source(template_name)
            source = self._tornado_template_code.sub('',source)
            self._CACHE[template_name] = source
            return source
