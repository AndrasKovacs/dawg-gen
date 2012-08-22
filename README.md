# DAWG generator #

Creates highly compressed acyclic word graphs from word lists.
See http://en.wikipedia.org/wiki/Trie and http://en.wikipedia.org/wiki/Directed_acyclic_word_graph for an overview of the data structure.

### Requirements

Python 2.7.

### Acknowledgement:

https://github.com/chalup/dawggenerator for piquing my interest and the basic idea of using hashes for sub-trie comparison.

### Usage:

Launch from console

    > dawg_gen.py [word list file]

Note that the word list must be sorted, delimited by space or newline and have uppercase words. The program will prompt you for the output location for the compressed DAWG. Searching algorithms are not included; you are free to write those, armed with an understanding of the data format described below. 

### Data format

The output is essentially an array of 32-bit integers. Each integer is a trie node encoding the following data fields:

- Index of first child: 	22 bits
- Value of character: 		8 bits
- End-of-children-list flag:    1 bit
- End-of-word flag:		1 bit

In a traditional trie, a node has a character value and a list of child nodes. The main difference (as far as the logical structure goes, the only notable difference) here is that nodes store only a pointer to their first child. This is all that is needed because the children are laid out next to each other in the array, thus iterating over them can be done by incrementing the node index until a node with the end-of-children-list flag set is found. A node that has no children points to a "null" node that has a invalid character value. Also, a root node pointing to the first child in the uppormost child list is always positioned at the very end of the array. This node also has an empty/invalid character value. 

For example, a trie containing "AD", "AN", and "AT" may look like this:


<table, border="1">
  <tr>
    <th>Index</th><th>Character</th><th>End-of-list</th><th>End-of-word</th><th>First child</th>
  </tr>
  <tr>
    <td>0</td><td>0</td><td>1</td><td>0</td><td>0</td>
  </tr>
  <tr>
    <td>1</td><td>D</td><td>0</td><td>1</td><td>0</td>
  </tr>
  <tr>
    <td>2</td><td>N</td><td>0</td><td>1</td><td>0</td>
  </tr>
  <tr>
    <td>3</td><td>T</td><td>1</td><td>1</td><td>0</td>
  </tr>
  <tr>
    <td>4</td><td>A</td><td>1</td><td>0</td><td>1</td>
  </tr>
  <tr>
    <td>5</td><td>0</td><td>1</td><td>0</td><td>4</td>
  </tr>
</table>

Here the root node points to "A", which in turn points to node 1, and starting from there we can get the other children of "A" by incrementing the index.

Note that only the root node has a fixed position; other nodes (including the null end-node) are laid out arbitrarily. Moreover, child lists are interleaved, for example, the child list "A", "B", "C", "D", may have a parent that points to "A" as first child, and another parent that points to "C". However, neither the interleaving nor the internal ordering change anything about the logical structure. 

### Compression preformance

The 178691-word TWL06 dictionary (http://www.isc.ro/lists/twl06.zip) is compressed to about 113980 nodes on my 2,66 gHz Core2 Duo computer in 9 seconds. There is another 1 second of safety checking of input and output in the program hosted here. There is a small variance in output size (see "Possible improvements"). 

### Implementation

Steps:

1. A trie is built from the words.

2. A hash-value is computed depth-first for all sub-tries. These hashes are stored in a hash table. Redundant nodes are discarded on the go.

3. Child lists of the remaining nodes are hashed into a table; redundant child lists are discarded by resetting the nodes' pointers to child lists.

4. For each child list it is determined whether some other child list is its strict superset. This will allow us to interleave multiple child lists into one by reordering the nodes. Checking all potential supersets for each child list would be prohibitive. For this reason an inverse hash table is generated: it has the unique trie nodes as keys and lists of child lists that contain the node as values. For each child list we only have to find the smallest relevant list of supersets, and go through that. This way, in the case of the TWL06 dictionary the average number of searches per child list is reduced from about 25000 to 6,7. The interleaving is done on a first-fit basis, where the the longest child lists and the longest possible supersets are tested first. 

5. Nodes are reordered in interleaved child lists. 

6. Child lists and nodes are mapped to a linear array, pointers are converted from memory addresses to array indices. 

7. The resulting array is converted to an array of bit-packed integers. 

### Possible improvements

* Currently there is a small (< 0,1%) variance in output size, most likely because the hashing of memory addresses changes across runs, which changes the iteration order of some hash tables. I haven't tracked down the exact cause of this; it'd be reassuring to eliminate this and optimize compression to the best cases of the variance.
* Doing a C++ port. I have a C++ implementation of a simpler algorithm that produces about 10% bigger output and runs in 390ms for the TWL06 dictionary. The Python version of that algorithm runs in 6,6 sec. A C++ port for the more complicated algorithm should produce a comparable speedup (though debugging such C++ often compromises my mental balance).
* Implementing the 3-byte node-packing. I think I'll do that shortly.  








