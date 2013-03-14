#!/usr/bin/env python

import os
import array as ar
import hashlib
from sys import argv
from copy import copy
from collections import defaultdict
from time import clock


######################## Read/check word list ###############################

print
if len(argv) != 2:
    print "Usage: dawg_gen.py [word list path]"
    exit(1)
filename = argv[1]
time = clock()
print "Checking word list...", 
try:
    wordlist = open(filename).read().split()
except IOError:
    print "File not found."
    exit(1)
if not all(all(c.isupper() for c in w) for w in wordlist) or any(b < a for a,b in zip(wordlist, wordlist[1:])):
    print
    print "Invalid word list; please include alphabetically sorted uppercase words delimited by space or newline."
    exit(1) 
print "OK".ljust(13),

  
print "finished in {:.4} seconds.".format(clock()-time)

######################## Build Trie #########################################

class SeqTrie(object):
    def __init__(self, init = tuple(), is_end = False, val = "", end_of_list = False):
        self.children = []
        self.is_end = is_end
        self.val = val
        self.end_of_list = end_of_list
        for x in init: 
            self.add(x)

    def add(self, word):
        for c in word:
            if not self.children or self.children[-1].val != c: #only works on pre-sorted word lists! 
                self.children.append(SeqTrie())
            self = self.children[-1]
            self.val = c
        self.is_end = True

    def __iter__(self):
        for x in self.children:
            for y in x.__iter__():
                yield y
        yield self


t = clock()
print "Building trie...".ljust(35),
trie = SeqTrie(wordlist)
print "finished in {:.4} seconds.".format(clock()-t)

################### Generate hashes/merge nodes,  ###########################

t = clock()
print "Merging redundant nodes...".ljust(35),

node_dict = {}
for x in trie:
    hash_str = "".join((str(x.is_end), x.val, "".join(y.hash for y in x.children)))
    x.hash = hashlib.md5(hash_str).digest()
    if x.hash not in node_dict: 
        node_dict[x.hash] = x
        for i,y in enumerate(x.children):
            x.children[i] = node_dict[y.hash]
        x.children = tuple(sorted(x.children))

clist_dict = {x.children: x.children for x in node_dict.itervalues()}

for x in node_dict.itervalues():
    x.children = clist_dict[x.children]


print "finished in {:.4} seconds.".format(clock()-t)


########################## Merge child lists ###############################

t = clock()
print "Merging child lists...".ljust(35),

inverse_dict = defaultdict(list)
compress_dict = {x:[x] for x in clist_dict.itervalues() if x}


for clist in clist_dict.itervalues():
    for node in clist:
        inverse_dict[node].append(clist)

for x in inverse_dict:
    inverse_dict[x].sort( key = lambda x: (len(x), sum(len(inverse_dict[y]) for y in x) ))

for clist in sorted(compress_dict.keys(), key = lambda x:(len(x), -1*sum(len(inverse_dict[y]) for y in x)), reverse=True):
    for other in min((inverse_dict[x] for x in clist), key = len):
        if compress_dict[other] and set(clist) < set(compress_dict[other][-1]):
            compress_dict[other].append(clist)
            compress_dict[clist] = False
            break

compress_dict = {x:l for x,l in compress_dict.iteritems() if l}

print "finished in {:.4} seconds.".format(clock()-t)


#################### Create compressed trie structure #######################
t = clock()
print "Creating compressed node array...".ljust(35),

end_node = SeqTrie(init = (), is_end = False, val = "", end_of_list = True)
end_node.children = ()

array = [0,]*(sum(len(x[0]) for x in compress_dict.itervalues()) + 1)
clist_indices = {}

array[0] = end_node
clist_indices[()] = 0

pos = 1
for stuff in compress_dict.itervalues():
    if len(stuff) > 1:
        sort = [0]*26
        for i, clist in enumerate(stuff):
            for y in clist:
                sort[ord(y.val) - ord('A')] = (i, y)
        stuff.append([n for i,n in sorted(x for x in sort if x)])
        for clist in stuff[:-1]:
            clist_indices[clist] = pos + len(stuff[0]) - len(clist)
    else:
        clist_indices[stuff[0]] = pos

    clist = stuff[-1]
    array[pos:pos+len(clist)] = map(copy, clist)
    pos += len(clist)
    array[pos-1].end_of_list = True

for x in array:
    x.children = clist_indices[x.children]

root = clist_indices[trie.children]
root_node = SeqTrie(init = (), is_end = False, val = "", end_of_list = True)
root_node.children = root
array.append(root_node)

print "finished in {:.4} seconds.".format(clock()-t)

######################### check trie ###################################

t = clock()
print "Checking output correctness...",


def extract_words(array, i=root, carry = ""):
    node = array[i]
    if not node.val:
        return
    while True:
        for x in extract_words(array, node.children, carry + node.val):
            yield x
        if node.is_end:
            yield carry + node.val
        if node.end_of_list: break
        i += 1
        node = array[i]

if set(extract_words(array)) == set(wordlist):
    print "OK".ljust(4), "finished in {:.4} seconds.".format(clock()-t)
else:
    print "INVALID OUTPUT: trie does not match original word list."
    exit(1)
print 
print "Compression finished in {:.4} seconds.".format(clock()-time)
print "Number of nodes:", len(array)
print


################## export as bitpacked array binaries #########################

def prompt_filename():
    while True:
        inp = raw_input("Enter export path: ")
        if os.path.exists(inp):
            while True:
                choice = raw_input("File already exists. Overwrite? ")
                if choice in ('y', 'Y'): return inp
                if choice in ('n', 'N'): break
        else:
            return inp


def prompt_packing_mode():
    ok_3b = len(array) <= 2**17
    ok_4b = len(array) <= 2**22
    while True:
        print
        print "Choose node size:"
        print "    (3) bytes" + " -> UNAVAILABLE: number of nodes above 2**17-1 or 131071"*(not ok_3b)
        print "    (4) bytes" + " -> UNAVAILABLE: number of nodes above 2**22-1 or 4194303"*(not ok_4b)
        print
        mode = raw_input("> ")
        if mode in ok_3b*"3" + ok_4b*"4":
            return mode


inp = prompt_filename()
mode = prompt_packing_mode()

t = clock()
print
print "Exporting as bit-packed array...",

if mode == "4":
    output = ar.array('L', [0]*len(array))

    for i,x in enumerate(array):
        output[i] |= (x.children << 10)
        output[i] |= ((ord(x.val) if x.val else 0) << 2)
        output[i] |= (x.end_of_list<<1)
        output[i] |= (x.is_end)
    outfile = open(inp, "wb")
    output.tofile(outfile)
    outfile.close()
    print "finished in {:.4} seconds.".format(clock()-t)

elif mode == "3":
    output = ar.array('B', [0]*(len(array)*3))

    for i,x in enumerate(array):
        i *= 3
        a, b, c = i, i+1, i+2
        output[a] = (x.children & 0b00000000011111111)
        output[b] = (x.children & 0b01111111100000000) >> 8
        output[c] = (x.children & 0b10000000000000000) >> 9
        output[c] |= ((ord(x.val) - ord('A') + 1 if x.val else 0) << 2) # 0 is reserved for root and end-of-trie nodes
        output[c] |= (x.end_of_list<<1)
        output[c] |= (x.is_end)

    outfile = open(inp, "wb")
    output.tofile(outfile)
    outfile.close()
    print "finished in {:.4} seconds.".format(clock()-t)

