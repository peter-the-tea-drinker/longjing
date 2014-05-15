#/usr/bin/env python

from __future__ import print_function

import tornado.web
import ui_modules
import os
import cProfile
from find_similar_files_slow import find_similar_files

import cProfile, pstats, StringIO
pr = cProfile.Profile()
pr.enable()
pr.runcall(find_similar_files,'main.py', os.getcwd(), 5, '*', SLOW=True)
pr.disable()
s = StringIO.StringIO()
stats = pstats.Stats(pr, stream=s)

from profile import Profile
import os

func_to_source = {}


def trace_dispatch(frame, event, arg):
    if event == 'call':
        import inspect
        fcode = frame.f_code
        if not (fcode.co_filename, fcode.co_firstlineno, fcode.co_name) in func_to_source:
            try:
                func_to_source[(fcode.co_filename, fcode.co_firstlineno, fcode.co_name)] = inspect.getsource(fcode)
            except:
                func_to_source[(fcode.co_filename, fcode.co_firstlineno, fcode.co_name)] = '#no source found'

import sys
sys.setprofile(trace_dispatch)
print('getting source (slow)')
find_similar_files('main.py', os.getcwd(), 5, '*', SLOW=True)
sys.setprofile(None)


class Handler(tornado.web.RequestHandler):
    def get(self,name=None):
        from tornado.escape import json_encode
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
                func_src = func_to_source[func]
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

'''

sections
    (reference source?)

source
    (referenced by web?)

func, (cc, nc, tt, ct, callers) = list(p.)[0]

       ncalls  tottime  percall  cumtime  percall
ncalls = nc / cc # number of calls, primative (non-recursive) calls
cumtime = ct
percall = ct/cc # cumulative time / primative calls
percall = tt/nc # total time / num calls
tottime = tt # total time

cc
nc
tt
cumtime
file
line
name
stdname


    [ 0] = Time that needs to be charged to the parent frame's function.
           It is used so that a function call will not have to access the
           timing data for the parent frame.
    [ 1] = Total time spent in this frame's function, excluding time in
           subfunctions (this latter is tallied in cur[2]).
    [ 2] = Total time spent in subfunctions, excluding time executing the
           frame's function (this latter is tallied in cur[1]).
    [-3] = Name of the function that corresponds to this frame.
    [-2] = Actual frame that we correspond to (used to sync exception handling).
    [-1] = Our parent 6-tuple (corresponds to frame.f_back).



    [0] = The number of times this function was called, not counting direct
          or indirect recursion,
    [1] = Number of times this function appears on the stack, minus one
    [2] = Total time spent internal to this function
    [3] = Cumulative time that this function was present on the stack.  In
          non-recursive functions, this is the total execution time from start
          to finish of each invocation of a function, including time spent in
          all subfunctions.
    [4] = A dictionary indicating for each function name, the number of times
          it was called by us.

"%8.3f"

filename, line, name = func
fname = os.path.basename(filename)



def func_strip_path(func_name):
    filename, line, name = func_name
    return os.path.basename(filename), line, name

'''

# want: script, attr = type="text/html"
if __name__ == '__main__':
      import sys
      import tornado.ioloop
      #import ui_modules
      port = '8080'

      #if len(sys.argv)<2:
     #        print 'usage: main.py 8080'
     # port = sys.argv[1]

      application = tornado.web.Application([
          tornado.web.url('/',Handler,name='Handler'),
          #tornado.web.url('/jellyfish/(.+)',Handler,name='Handler')
      ],
          xsrf_cookies=True,
          cookie_secret = "cookie secret",
          template_path = './templates',
          static_path = './static',
          ui_modules = ui_modules,
          # SECURITY NOTICE
          # It's horrbile practice to get the domain from the request, because that can be forged.
          # I'm manually entering the domain into torando's settings, so I can lock it down.
          domain = '127.0.0.1:8080',
          #ui_modules=ui_modules
          )

      application.listen(int(port))
      tornado.ioloop.IOLoop.instance().start()
