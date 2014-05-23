#/usr/bin/env python

from __future__ import print_function

'''Usage:

import statserver
import mymodule
statserver.profile(mymodule.func, arg1, arg2, kwarg=val)

This will call mymodule.func(arg1, arg2, kwarg=val), profile it,
serve the profile on localhost:9876, and open your webbrowser to view
the profile.

There are no dependencies, but the online profile uses external CSS and
Javascript assets to make the page look prettier.

It should be fine on Python 2, and Python 3. It can handle unicode
in files, and even unicode in file names.
'''


# ugly imports, to support Python 2 and 3
try:
    import  BaseHTTPServer
    # Python 2
    def as_buffer(s):
        return s
except:
    import http.server as BaseHTTPServer
    # Python 3
    def as_buffer(s):
        return s.encode('utf8')

try:
    import urlparse
except:
    import urllib.parse as urlparse

import urllib
try:
    quote = urllib.quote
    unquote = urllib.unquote
except:
    quote = urllib.parse.quote
    unquote = urllib.parse.unquote

import re
import os

def profile(func, *args, **kwargs):
    import webbrowser
    stats = get_stats(func, *args, **kwargs)
    server = BaseHTTPServer.HTTPServer(('localhost', 9876), StatsHandler)
    server.stats = stats
    print('Use <Ctrl-C> to stop')
    webbrowser.open('localhost:9876')
    server.serve_forever()


def get_stats(func, *args , **kwargs):
    '''Runs Python's profiler, and returns a pStats object'''
    import cProfile, pstats
    try:
        import cStringIO
        s = cStringIO.StringIO()
    except:
        import io
        s = io.StringIO
    print('profiling')
    pr = cProfile.Profile()
    pr.enable()
    pr.runcall(func, *args , **kwargs)
    pr.disable()

    stats = pstats.Stats(pr, stream=s)
    print('finished profiling')
    stats_dict = {}
    for pStat in stats.stats.items():
        stat = Stat(pStat)
        stats_dict[stat['function_definition']] = stat
    return stats_dict

def function_definition(func):
    '''Creates a string from a pStats function definition.'''
    filename, line, name = func
    return "%s:%i:%s"%(filename, line, name)

def f_to_s(f):
    '''Format a float as a string, in ms'''
    return "%.4g ms"%(f*1000)

def escape(s):
    import cgi
    return cgi.escape(s)

def url_escape(s):
    import cgi
    return cgi.escape(quote(s,safe=''))

def url_unescape(s):
    return escape(unquote(s))

class Stat(dict):
    '''Creates an object representing theh profile of a
    function. It is a superclass of "dict", so that it
    can be easily formatted.'''
    def __init__(self, pstat):
        super(Stat, self).__init__()
        func, (cc, nc, tt, ct, callers)  = pstat
        self.init_stats(cc, nc, tt, ct)

        self['function_definition'] = escape(function_definition(func))

        filename, line, name = func

        self['line'] = line
        self['name'] = escape(name)
        self['filename'] = escape(filename)
        self['base_file'] = escape(os.path.basename(filename))
        self['link'] = '/function/'+url_escape(function_definition(func))

        source = self.get_source(filename, line)
        self['no_source_warning'] = ''
        if not source:
            self['no_source_warning'] = '(no source)'
            source = '# no source found'
        self['source'] = escape(source)

        # caller definitions won't be used in formatting directly, so it won't
        # need to be in the dict
        self.caller_definitions = [escape(function_definition(c)) for c in callers]

    def init_stats(self, cc, nc, tt, ct):
        '''Create more useful statistics, mostly based on
        Python's profile.py source.
        '''
        # total function calls
        self['n_calls'] = nc

        # primative (non-recursive) calls
        self['p_calls'] = cc

        # cumulative time
        self['cumtime'] = ct
        self['cumtime_str'] = f_to_s(ct)

        # Per call cumulative time
        # Division by non-recursive calls.
        # If it were divided by total calls, then
        # recursive functions would look faster
        percall_c = ct/cc
        self['percall_c'] = percall_c
        self['percall_c_str'] = f_to_s(percall_c)

        # Per call internal time
        # Division by total calls, not non-recursive calls
        percall_f = tt/nc
        self['percall_f'] = percall_f
        self['percall_f_str'] = f_to_s(percall_f)

        self['tottime'] = tt
        self['tottime_str'] = f_to_s(tt)


    func_definition_re = re.compile(r'^(\s*def\s)|(.*(?<!\w)lambda(:|\s))|^(\s*@)')

    def get_source(self, filename, first_line_num):
        '''see python's inspect.py - this gets the source from
        a Python source file, given the file name and first line number'''
        import inspect
        try:
            lines = inspect.linecache.getlines(filename)
            line_num = first_line_num - 1
            while line_num > 0:
                if self.func_definition_re.match(lines[line_num]):
                    break
                lnum = lnum - 1
            return '\n'.join(inspect.getblock(lines[line_num:]))
        except:
            return ''

    def as_row(self):
        return '''    <tr><td><a href={link}>{name}</a> {no_source_warning}</td>
            <td>{n_calls} / {p_calls}</td>
            <td>{cumtime_str}</td>
            <td>{percall_c_str}</td>
            <td>{percall_f_str}</td>
            <td>{tottime_str}</td>
            <td>{filename}</td>
            '''.format(**self)

    def as_div(self, all_function_profiles):
        callers = [all_function_profiles[c] for c in self.caller_definitions]
        callers = sorted(callers, key=lambda k: k['cumtime'])
        callers_list = '        \n'.join([c.as_list_item() for c in callers])
        function_template = '''
        <div>
        <table class="pure-table pure-table-horizontal">
        <tbody>
        <tr><td>Name</td><td>{name}</td></tr>
        <tr><td>Filename</td><td>{filename}:{line}</td></tr>
        <tr><td>Cumulative time</td><td>{cumtime_str}</td></tr>
        <tr><td>Cumulative time / call</td><td>{percall_c_str}</td></tr>
        <tr><td>Internal time / call</td><td>{percall_f_str}</td></tr>
        <tr><td>Internal time</td><td>{tottime_str}</td></tr>
        </tbody>
        </table>
        <ul>
        {callers_list}
        </ul><br>
        <pre><code data-language="python">{source}</code></pre></div>
        '''
        return function_template.format(callers_list = callers_list, **self)

    def as_list_item(self):
        template = ('<li><a href="{link}">{name}</a> {no_source_warning}'
                    'Time: {cumtime_str}</li>')
        return template.format(**self)


base_template = '''<!DOCTYPE html>
<html lang="en">
      <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{title}</title>
<link rel="stylesheet" href="http://yui.yahooapis.com/pure/0.4.2/pure.css">
<link href="//cdnjs.cloudflare.com/ajax/libs/rainbow/1.2.0/themes/tomorrow-night.css" rel="stylesheet" type="text/css">
{style}
</head>
<body>
<h1>{title}</h1>
{body}
</body>
<script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
<script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/rainbow/1.2.0/js/rainbow.min.js"></script>
<script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/rainbow/1.2.0/js/language/generic.js"></script>
<script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/rainbow/1.2.0/js/language/python.js"></script>
<script type="text/javascript">
Rainbow.color();
</script>
</html>'''

sorted_stats_table_template = '''
<table class="pure-table pure-table-horizontal">
<thead>
    <tr>
        <th><a href="/name">Function</a></th>
        <th><a href="/n_calls">Calls</a> / <a href="p_calls">Non-recursive calls</a></th>
        <th><a href="/cumtime">Cumulative time</a></th>
        <th><a href="/percall_c">Cumulative time / call</a></th>
        <th><a href="/percall_f">Internal time / call</a></th>
        <th><a href="/tottime">Internal Time</a></th>
        <th><a href="/filename">File</a></th>
    </tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
'''
style = '''<style>
body
{
padding:5em;
}
</style>'''

class StatsHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.stats = self.server.stats
        if not self.path or self.path=='/':
            return self.serve_sorted_stats('cumtime')

        path = self.path.split('/')
        if len(path)==2:
            method = path[1]
            if method!='favicon.ico':
                return self.serve_sorted_stats(method)

        if len(path)==3:
            if path[1] == 'function':
                function_name = url_unescape(path[2])
                if function_name in self.stats:
                    return self.serve_function(function_name)

        self.send_response(404)
        self.end_headers()
        self.wfile.write('Not found')
        return

    def serve_sorted_stats(self, method):
        def sort_key(stat_dict):
            return (stat_dict[method],
                     stat_dict['cumtime'],
                     stat_dict['function_definition'])
        reverse = True
        if method in ('name','filename'):
            reverse = False
        stats = sorted(self.stats.values(), key=sort_key, reverse=reverse)
        rows = '\n'.join(stat.as_row() for stat in stats)
        body = sorted_stats_table_template.format(rows=rows)
        html = base_template.format(title=method, body=body, style=style)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(as_buffer(html))

    def serve_function(self,function_name):
        stat = self.stats[function_name]
        body = stat.as_div(self.stats)
        html = base_template.format(title=stat['name'], body=body, style=style)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(as_buffer(html))

def test_func(arg1, n=None):
    re.compile('whatever|.*')

if __name__ == '__main__':
    profile(test_func)
