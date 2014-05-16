#/usr/bin/env python

from __future__ import print_function
import tornado.web
import re

PORT = 8080

def serve_profile(function, *args, **kwargs):
    '''Serve a pofile on localhost:8080.

    func: the function to profile

    *args: the arguments to the function

    ** kwargs: the keyword arguments

    For example: serve_profile(find_similar_files,'main.py', os.getcwd(), 5, '*', SLOW=True)
    will profile this: find_similar_files('main.py', os.getcwd(), 5, '*', SLOW=True)

    By default, the port will be 8080. To change it it, do something like this:

    import main
    main.PORT=9000
    '''
    import cProfile, pstats, StringIO
    pr = cProfile.Profile()
    pr.enable()
    pr.runcall(find_similar_files,'main.py', os.getcwd(), 5, '*', SLOW=True)
    pr.disable()
    s = StringIO.StringIO()
    stats = pstats.Stats(pr, stream=s)
    serve(stats)

def serve(stats):
    import tornado.ioloop
    import ui_modules

    application = tornado.web.Application([
        tornado.web.url('/',Handler,name='Handler',kwargs = {'stats':stats}),
        ],
        xsrf_cookies=True,
        cookie_secret = "cookie secret",
        template_path = './templates',
        static_path = './static',
        ui_modules = ui_modules,
        )

    application.listen(int(PORT))
    tornado.ioloop.IOLoop.instance().start()

class Handler(tornado.web.RequestHandler):
    def initialize(self,stats):
        self.stats = stats

    def get(self,name=None):
        import os
        from tornado.escape import json_encode

        stats = self.stats

        func_to_sid = {}
        func_items = {}
        sid = 0
        for stat in stats.stats.iteritems():
            func_to_sid[stat[0]] = sid
            sid+=1

        for stat in stats.stats.iteritems():
            func, (cc, nc, tt, ct, callers) = stat
            sid = func_to_sid[func]
            n_calls = nc
            p_calls = cc # number of calls, primative (non-recursive) calls
            cumtime = ct*1000
            percall_c = ct/cc*1000 # cumulative time / primative calls
            percall_f = tt/nc*1000 # total time / num calls
            tottime = tt*1000 # total time
            filename, line, name = func
            try:
                func_src = get_source_from_func(filename,line)
                json_encode(func_src) # just in case there's any errors (Unicode?)
            except:
                func_src = '#no source found'
            filename = os.path.basename(filename)
            callers = [func_to_sid[f] for f in callers]
            func_items[sid] = dict(sid = sid,
                                   n_calls = n_calls,
                                   p_calls = p_calls,
                                   cumtime = "%.4g"%cumtime,
                                   percall_c = "%.4g"%percall_c,
                                   percall_f = "%.4g"%percall_f,
                                   tottime = "%.4g"%tottime,
                                   filename = filename,
                                   line = line,
                                   name = name,
                                   func_src = func_src,
                                   callers = callers,
                                   schema = 'stat')

        itemsJSON = json_encode(func_items.values())

        def get_sort_order(name):
            stats.sort_stats(name)
            sort_order = []
            for fcn in stats.fcn_list:
                sid = func_to_sid[fcn]
                sort_order.append(sid)
            return sort_order

        cumulativeJSON = json_encode(get_sort_order('cumulative')[:50])
        callsJSON = json_encode(get_sort_order('calls')[:50])
        pcallsJSON = json_encode(get_sort_order('pcalls')[:50])
        time = get_sort_order('time')[:50];
        timeJSON = json_encode(time)

        items = [func_items[sid] for sid in time[:10]]
        items[0]['mode'] = 'detail'
        for item in items[1:]:
            item['mode'] = 'summary'
        self.render('stats.html',items=items, cumulativeJSON=cumulativeJSON,
        callsJSON=callsJSON, timeJSON = timeJSON, pcallsJSON=pcallsJSON, itemsJSON=itemsJSON)

func_definition = re.compile(r'^(\s*def\s)|(.*(?<!\w)lambda(:|\s))|^(\s*@)')
def get_source_from_func(filename,first_line_num):
    "see python's inspect.py"
    import inspect
    lines = inspect.linecache.getlines(filename)
    line_num = first_line_num - 1
    while line_num > 0:
        if func_definition.match(lines[line_num]):
            break
        lnum = lnum - 1
    return '\n'.join(inspect.getblock(lines[line_num:]))

if __name__ == '__main__':
    import os
    from find_similar_files import find_similar_files
    serve_profile(find_similar_files,'main.py', os.getcwd(), 5, '*', SLOW=True)
