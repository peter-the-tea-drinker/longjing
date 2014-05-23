import tornado.web
import re, os

class Todo(tornado.web.UIModule):
    def render(self,todo):
        return self.render_string('todo.html',todo=todo)

class KOTemplate(tornado.web.UIModule):
    def _get_template_source(self,template_name):
        from tornado.web import RequestHandler
        # see UIModule's source
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
        
    _tornado_template_code = re.compile('({%.*?%})|{#(.*?)#}|{{(.*?)}}')
    _CACHE = {}
    def render(self,template_name):
        try:
            return _CACHE[template_name]
        except:
            source = self._get_template_source(template_name)
            source = self._tornado_template_code.sub('',source)
            self._CACHE[template_name] = source
            return source
