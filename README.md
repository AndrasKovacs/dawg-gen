# DAWG generator #


Creates highly compressed directed acyclic word graphs from word lists.
See http://en.wikipedia.org/wiki/Trie and http://en.wikipedia.org/wiki/Directed_acyclic_word_graph for an overview of the data structure.


### Requirements


Python 2.7.


### Acknowledgement


https://github.com/chalup/dawggenerator for piquing my interest and the basic idea of using hashes for sub-trie comparison.


### Usage


Launch from console:

    $ dawg_gen.py [word_list file]

Note that the word list must be sorted, delimited by space or newline and have uppercase words. The program will prompt you for 

- The output location.
- Whether you choose 3- or 4-byte nodes (if available).

Searching algorithms are not included; you are free to write those, armed with an understanding of the data format described below. 


### Data format


The output is an array of 3- or 4-byte binary chunks. Each chunk encodes a trie node containing the following fields:

- Index of first child
- Value of character
- End-of-children-list flag
- End-of-word flag

In a traditional trie, a node has a character value and a list of child nodes. The main difference (as far as the logical structure goes, the only notable difference) here is that nodes store only a pointer to their first child. This is all that is needed because the children are laid out next to each other in the array, thus iterating over them can be done by incrementing the node index until a node with the end-of-children-list flag set is found. A node that has no children has "0" as child index. This implies that the "0" position in the array is invalid and should not be dereferenced. The root node is always positioned at the end of the array and has '\0' as character value.

For example, a trie containing "AD", "AN", and "AT" may look like this:


<table>
  <tr>
    <th>Index</th><th>Character</th><th>End-of-list</th><th>End-of-word</th><th>First child</th>
  </tr>
  <tr>
    <td>0</td><td>0</td><td>1</td><td>1</td><td>0</td>
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

Here the root node points to "A", which in turn points to node 1, and starting from there we can get the other children of "A" by incrementing the index.Note that only the root node (last node) and end node (first node) have predetermined positions. 


### 3- vs. 4-byte nodes


Bit layout:

<table cellpadding="10">
  <tr>
    <th></th><th>3 byte</th><th>4 byte</th>
  </tr>
  <tr>
    <td>First child</td><td>17</td><td>22</td>
  </tr>
  <tr>
    <td>Character</td><td>5</td><td>8</td>
  </tr>
  <tr>
    <td>End-of-list</td><td>1</td><td>1</td>
  </tr>
  <tr>
    <td>End-of-word</td><td>1</td><td>1</td>
  </tr>
</table>

Notes:

- The maximum number of indexable nodes is 2^17 - 1 = 131071 and 2^22 - 1 = 4194303 respectively.

- In the case of 3-byte nodes, the character values are shifted down to the [1,26] range (0 is reserved for root and end nodes). With 4-byte nodes the ASCII values are preserved.

- The first child index is laid out in little endian order in the 3-byte node.

- Tip for handling 3-byte nodes in C/C++: create a struct with an unsigned char array to hold the data, then create another struct with the appropriate bitfields for the node layout. Cast a "data" struct pointer to the "wrapper" struct to read and write the contents with the simple bitfield syntax. Make sure to never try to access the last byte of the wrapper.


### Compression preformance


The 178691-word TWL06 dictionary (http://www.isc.ro/lists/twl06.zip) is compressed to about 113735 nodes on my 2,66 GHz Core2 Duo computer in 9,1 seconds. There is another 1 second of safety checking of input and output in the program hosted here. There is a very small variance (< 0,001%) in the number of nodes, most likely because the hashing of memory addresses varies across runs, slightly changing iteration order when interleaving child lists. 


### Implementation


Steps:

1. A trie is built from the word list.

2. A hash value is computed depth-first for all sub-tries. These hashes are stored in a hash table. Redundant nodes are discarded on the go by checking if a node is already in the hash table.

3. The child lists of the remaining nodes are hashed into a table; redundant child lists are discarded.

4. For each child list it is determined whether some other child list is its strict superset. This will allow us to interleave multiple child lists into one by reordering the nodes. Checking all potential supersets for each child list would be prohibitive. For this reason an inverse hash table is generated: it has the unique trie nodes as keys and lists of child lists that contain the node as values. For each child list we only have to find the smallest list of potential supersets, and go through that. This way, in the case of the TWL06 dictionary the average number of superset checks per child list is reduced from about 25000 to 6,7. The superset checking is done in a way such that the longest child lists with the rarest elements are tested against the shortest possible supersets with the rarest elements. I compute the approximate "rarity" of a child list by summing the length of the inverse dictionary list for each of its element nodes. This way the small and common child lists don't eat up space before the more difficult child lists have had their chances. 

6. Child lists and nodes are mapped to an array, pointers are converted from memory addresses to array indices. In the meanwhile, nodes are reordered in interleaved child lists. 

7. The resulting array is converted to an array of bit-packed integers. 


### Possible improvements


- Doing a C++ port. I have a C++ implementation of a simpler algorithm that produces about 10% bigger output and runs in 390ms for the TWL06 dictionary. The Python version of that algorithm runs in 6,6 sec. A C++ port for the more complicated algorithm should produce a comparable speedup.

- Compressing chains of nodes where each node has only one child. For example, 


<pre>
           e
          /
a->b->c->d 
          \
           f
</pre> 

would become

<pre>
       e
      /
[abcd]
      \
       f
</pre>


The compressed nodes would need only one pointer at the end of the chain. The minimum size of indices would have to grow though since each character inside a [xxx] would have to be pointable to (the size of indices would then grow because they'd have to point to one-byte blocks or have extra bits for indexing nodes inside a [xxx]).

### License

MIT.




