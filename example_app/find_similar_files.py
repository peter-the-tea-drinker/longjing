from __future__ import print_function

def find_similar_files(main_file, search_dir, n, criteria, SLOW=False):
    from difflib import SequenceMatcher
    import fnmatch
    import os

    main_seq = open('main.py').read()
    best_files = [(0.0,None)]*n
    matcher = SequenceMatcher()
    if SLOW:
        matcher.set_seq1(main_seq) # XXX setting seq1 repeatedly is faster.
    else:
        matcher.set_seq2(main_seq) # it's faster to set seq2 once, and seq1 many times

    # recursive walk, from http://stackoverflow.com/questions/2186525/use-a-glob-to-find-files-recursively-in-python
    matches = []
    for root, dirnames, filenames in os.walk(search_dir):
        for filename in fnmatch.filter(filenames, criteria):
            fname = os.path.join(root, filename)
            try:
                seq = open(fname).read()
            except:
                continue # can't open
            if SLOW:
                matcher.set_seq2(seq)
            else:
                matcher.set_seq1(seq)
            ratio = matcher.quick_ratio()
            if ratio > best_files[0][0]:
                ratio = matcher.ratio()
                if ratio > best_files[0][0]:
                    best_files[0] = (ratio,fname)
                    best_files.sort()

    for (ratio,fname) in best_files[::-1]:
        print(ratio,fname)

if __name__=='__main__':
    # todo = make this more flexible
    pass
