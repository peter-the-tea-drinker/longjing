# not used now.

import difflib
import glob
import os
import re
import tornado.escape
code_folder = 'code/'
doc_folder = 'doc/'
folders = sorted(glob.glob(code_folder+'*'))

last_files = {}
filter = re.compile('.*\.py$|.*\.html$')
for folder in folders:
    # if no todo file exists, create one.
    result = ''
    all_files = ''
    try:
        old_tutorial = open(os.path.join(doc_folder,os.path.relpath(folder,code_folder))+'.html','rb').read().decode('utf8')
    except:
        open(os.path.join(doc_folder,os.path.relpath(folder,code_folder))+'.html','wb')
        old_tutorial = ''
    for root, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            if not filter.match(filename):
                continue
            path = os.path.join(root,filename)
            a = last_files.get(filename,'')
            b = tornado.escape.xhtml_escape(open(path,'rb').read().decode('utf8'))
            all_files += filename + '\n' + b + '\n\n\n'
            last_files[filename] = b
            matcher = difflib.SequenceMatcher(a=a,b=b,autojunk=False)

            for (tag, i1, i2, j1, j2) in matcher.get_opcodes():
                if not tag == 'equal':
                    code_a = a[i1:i2]
                    code_b = b[j1:j2]
                    for code in (code_a, code_b):
                        if not code in old_tutorial:
                            result+=tag+'\n\n'+code_a+'\n\n'+code_b+'\n\n'
    open(os.path.join(doc_folder,os.path.relpath(folder,code_folder))+'-all.txt','wb').write(all_files.encode('utf8'))
    if result:
        open(os.path.join(doc_folder,os.path.relpath(folder,code_folder))+'-todo.txt','wb').write(result.encode('utf8'))
