#

from __future__ import print_function

def find_similar_files(main_file, search_dir, n, criteria):
    from difflib import SequenceMatcher
    import fnmatch
    import os

    main_seq = open(main_file).read()

    # initialize the best files as 0 similarity, no file name
    best_files = [(0.0,None)]*n
    matcher = SequenceMatcher()
    matcher.set_seq2(main_seq) # it's faster to set seq2 for the main file

    # recursive walk
    for root, dirnames, filenames in os.walk(search_dir):
        for filename in fnmatch.filter(filenames, criteria):
            fname = os.path.join(root, filename)
            try:
                seq = open(fname).read()
            except:
                continue # can't open
            matcher.set_seq1(seq)
            # compare the similarity to the worst of the best n files
            ratio = matcher.quick_ratio()
            if ratio > best_files[0][0]:
                ratio = matcher.ratio()
                if ratio > best_files[0][0]:

                    # if this file is better than the worst of the best n,
                    # add it to the list of best files.
                    best_files[0] = (ratio,fname)

                    # now sort the best files by similarity.
                    best_files.sort()

    return best_files[::-1]

if __name__=='__main__':
    import argv
    if len(argv)
