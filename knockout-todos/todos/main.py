# -*- coding: utf-8 -*-

import tornado.web, tornado.ioloop
from collections import namedtuple, OrderedDict
import ui_modules
from tornado.escape import json_encode

class Todo(namedtuple('Todo',
           ('todo_id','todo_content',
           'todo_is_done','todo_state'))):
    __slots__ = ()
    @property
    def is_done_indicator(self):
        return '✓' if self.todo_is_done else '☐'

    @property
    def checked_attr(self):
        return  'checked' if self.todo_is_done else ''
todo_database = OrderedDict()
for i in range(1,10):
    todo_content = 'Todo Number %i'%i
    todo_is_done = bool(i%2) # alternate True / False
    todo_database[i]=Todo(i,todo_content, todo_is_done, 'todo_get')
class BaseHandler(tornado.web.RequestHandler):
    @property
    def is_ajax(self):
        if "X-Requested-With" in self.request.headers:
            x_requested_with = self.request.headers['X-Requested-With']
            if x_requested_with == "XMLHttpRequest":
                return True
        return False
class TodoListHandler(BaseHandler):
    def get(self):
        todos = todo_database.values()
        if self.is_ajax:
            self.content_type = 'application/json'
            result = {'todos':[todo._asdict() for todo in todos]}
            return self.finish(result)
        todosJSON = json_encode([todo._asdict() for todo in todos])
        self.render('todo-list.html', todos = todos,
                    todosJSON=todosJSON)
    def post(self):
        new_content = self.get_argument('todo_content','')
        new_is_done = self.get_argument('todo_is_done',False)
        i= len(todo_database)+1
        updated_todo = Todo(i, new_content, new_is_done, 'todo_get')
        todo_database[i]=updated_todo
        return self.get()
class TodoHandler(BaseHandler):
    def get(self, todo_id):
        i = int(todo_id)
        todo = todo_database.get(i,None)
        if not todo:
            raise tornado.web.HTTPError(404)
        editable_todo = todo._asdict()
        editable_todo['todo_state'] = 'todo_edit'
        editable_todo = Todo(**editable_todo)
        self.render('todo-list.html', todos = [editable_todo],
                    todosJSON=json_encode([editable_todo._asdict()]))
    def post(self, todo_id):
        i = int(todo_id)
        todo = todo_database.get(i,None)
        if not todo:
            raise tornado.web.HTTPError(404)
        new_content = self.get_argument('todo_content','')
        new_is_done = self.get_argument('todo_is_done',False)
        updated_todo = Todo(i, new_content, new_is_done, 'todo_get')
        todo_database[i]=updated_todo
        if self.is_ajax:
            self.content_type = 'application/json'
            todos = todo_database.values()
            result = {'todos':[todo._asdict() for todo in todos]}
            return self.finish(result)
        else:
            self.redirect('/todos/')
class SearchHandler(BaseHandler):
    def get(self):
        query = self.get_argument('query','')
        query = query.lower()
        todos = todo_database.values()
        todos = [t for t in todos if query in t.todo_content.lower()]
        result = [todo._asdict() for todo in todos]
        if self.is_ajax:
            self.content_type = 'application/json'
            return self.finish({'todos':result})
        self.render('todo-list.html', todos = todos,
                    todosJSON=json_encode(result))
urls = [
    # services
    ('/',TodoListHandler),
    ('/todos/',TodoListHandler),
    ('/search/', SearchHandler),

    # models
    ('/todos/([0-9]+)',TodoHandler)
]
application = tornado.web.Application(
    urls,
    template_path = './template',
    ui_modules = ui_modules,
    debug=True
    )

import tornado.log, sys, logging
tornado.log.access_log.addHandler(logging.StreamHandler(sys.stdout))
tornado.log.access_log.setLevel(logging.DEBUG)

application.listen(8888)
tornado.ioloop.IOLoop.instance().start()
