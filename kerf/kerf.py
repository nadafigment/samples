#!/usr/bin/env python

import sys
import copy

# for array support
import numpy

from Bio import SeqIO
from Bio import Phylo

class ArgError(Exception):
    '''Error in parsing arguments'''
    pass

class ParseError(Exception):
    '''Error in parsing files'''
    pass

class KerfError(Exception):
    '''General error for this module'''
    pass

# some predifined values -- ideally these would be options
# passed into the module or command-line, but we want at least
# to not have magical values within the code
MSA_SUFFIX = 'a2m'
MSA_FORMAT = 'fasta'
INPUT_PHYLO_FORMAT = 'newick'
OUTPUT_PHYLO_SUFFIX = 'xml'
OUTPUT_PHYLO_FORMAT = 'phyloxml'
GAP_CHAR = '-'


def percent_identity_value(lhs_msa, rhs_msa):
    '''
    Compute the percent identity value between the two given MSAs
    both of these arguments are Bio.SeqRecord objects

    Arguments:
     - lhs_msa: left-hand-side MSA, a Bio.SeqRecord object
     - rhs_msa: right-hand-side MSA, a Bio.SeqRecord object

    we return a float X, 0 <= X <= 1
    '''
    if len(lhs_msa) != len(rhs_msa):
        raise KerfError('mismatched MSA lengths!')

    # percent identity is defined as the number of exact matches divided by
    # the number of pairwise alignments, that is the number of columns where
    # not both characters are gap characters
    numerator = 0
    denom = 0

    # let's work with strings directly, should be quicker
    lhs_str = str(lhs_msa.seq)
    rhs_str = str(rhs_msa.seq)

    for i in xrange(len(lhs_str)):
        lhs_c, rhs_c = lhs_str[i], rhs_str[i]
        # we consider this column only if both lhs and rhs chars are not the GAP char
        if (lhs_c != GAP_CHAR) or (rhs_c != GAP_CHAR):
            denom = denom + 1
            if lhs_c == rhs_c:
                numerator = numerator + 1

    if denom == 0:
        # this shouldn't happen, should it?
        raise KerfError("Could not compute pairwise sequence identity for "
                        "'%s' and '%s' -- zero denominator!"
                        % (lhs_msa.name, rhs_msa.name))
    else:
        return numerator/float(denom)


class PercentIdentityMatrix(object):
    ''' PercentIdentityMatrix stores the pairwise percent identity values
    for all pairs of MSAs.
    Making a class for this is not strictly necessary but will make the code
    more readable and easier to maintain'''
    
    def __init__(self, msas):
        '''init method

        Arguments:
         - msas: the list (or iterable) of MSA Bio.SeqRecord objects on which we
                 will calculate pairwise sequence identity
        '''
        # cache this for quick reference
        self._size = len(msas)
        # we store the percent identity value for a pair of MSAs in an array
        # for quick and easy reference
        # (numpy.zeros gives us an empty array)
        # (This is wasteful, as we're only storing values in less than half of the array.
        #  but we'll only have one of these so we don't care so much)
        self._value_matrix = numpy.zeros((self._size, self._size))

        for row in xrange(self._size):
            for col in xrange(self._size):
                # we're really only concerned with the lower half of the matrix
                if col >= row:
                    continue                    
                self._value_matrix[row][col] = percent_identity_value(msas[row], msas[col])


    @property
    def size(self):
        '''Get the size of the matrix'''
        return self._size


    def pairwise_identity_value(self, lhs_index, rhs_index):
        '''
        Get the pairwise identity value for the given indicies

        Arguments:
         - lhs_index: the integer index (into the input list of MSAs) for the lhs MSA
         - rhs_index: the integer index (into the input list of MSAs) for the lhs MSA

        Returns the percent identity float value for the given indicies
        '''
        assert lhs_index != rhs_index
        assert lhs_index < self._size
        assert rhs_index < self._size
        if lhs_index > rhs_index:
            return self._value_matrix[lhs_index][rhs_index]
        else:
            return self._value_matrix[rhs_index][lhs_index]

        
    def index_sum(self, index):
        '''
        index sum is defined to be the sum of the pairwise values
        where the given index contributes
        '''
        sum_ = 0.0
        for other_index in xrange(self.size):
            if index == other_index:
                continue
            sum_ = sum_ + self.pairwise_identity_value(index, other_index)
        return sum_


class KerfHelper(object):
    '''
    A helper class that helps keep track of some of the info that we'll
    need to access as we work through the tree.

    It stores the set of pairwise sequence identity values (and provides
    handy/quick means of accessing that), as well as keeping track of the
    mapping between the names of the MSAs we get from the MSA list file
    and the names that appear in the newick tree file

    It also keeps track of the order we should traverse nodes from
    '''

    def __init__(self, msas, tree):
        '''Constructor

        Arguments:
         - msas: originally input list of MSA Bio.SeqRecord objects
         - tree: original input Phylo.TreeElement
        '''
        self.tree = tree
        self.identity_matrix = PercentIdentityMatrix(msas)
        self.node_name_to_index_dict = {}
        self.index_to_node_name_dict = {}
        self._fill_correlation_dicts(msas, tree)
        self.index_weights = []
        for idx in xrange(len(msas)):
            self.index_weights.append(self.identity_matrix.index_sum(idx))

            
    def next_traverse_node(self, processed_nodes):
        '''determine which node in the tree we should traverse next

        Arguments:
         - processed_nodes: list of nodes (Bio.Phylo.TreeElement) that we've already covered
        '''
        while True:
            idx = self._next_traverse_index()
            if idx == -1:
                # break condition -- we've nothing left to consider
                return None
            
            assert idx in self.index_to_node_name_dict
            node_name = self.index_to_node_name_dict[idx]

            matches = self.tree.find_elements(name=node_name, terminal=True)
            try:
                node = matches.next()
            except StopIteration:
                # this is a legal case -- we may have removed that node already
                continue
            else:
                if node in processed_nodes:
                    # we've done that one already -- keep looking
                    continue
                else:
                    # and we should make sure there is *only one* match
                    return node
        return None

    
    def can_add(self, node, added_nodes, cutoff_value):
        '''test for whether we can add the given node

        Arguments:
         - node: the node to add Phylo.TreeElement
         - added_nodes: list of Phylo.TreeElement objects that has already been processed
         - cutoff_value: float value indicating cutoff percent we're willing to keep
        '''
        assert node.name
        # this will raise if the name's not there
        node_idx = self.node_name_to_index_dict[node.name]

        added_indicies = []
        for node in added_nodes:
            if node.name:
                added_indicies.append(self.node_name_to_index_dict[node.name])
                                  
        for idx in added_indicies:
            identity_value = self.identity_matrix.pairwise_identity_value(node_idx, idx)
            if identity_value < cutoff_value:
                return False

        return True

    
    def _next_traverse_index(self):
        '''
        Used to determine which node in the tree we should traverse next
        internal method, easily switch between different strategies.
        don't see a difference in light testing -- using the max should encourage
        larger trees at the outset (and practice does show this)
        '''
        return self._next_traverse_index_max()

    
    def _next_traverse_index_min(self):
        '''
        find the min summed value in our set
        '''
        min_index, min_value = -1, -1.0

        for idx, val in enumerate(self.index_weights):
            # -1 indicates we've already used that one
            if val != -1:
                if min_value == -1 or val < min_value:
                    min_value = val
                    min_index = idx

        # we clear out this one to indicate we shouldn't choose it next time
        if min_index != -1:
            self.index_weights[min_index] = -1
            
        return min_index

    
    def _next_traverse_index_max(self):
        '''
        find the max summed value in our set
        '''
        max_index, max_value = -1, -1.0

        for idx, val in enumerate(self.index_weights):
            # -1 indicates we've already used that one
            if val != -1:
                if val > max_value:
                    max_value = val
                    max_index = idx

        # we clear out this one to indicate we shouldn't choose it next time
        if max_index != -1:
            self.index_weights[max_index] = -1
            
        return max_index

        
    def _fill_correlation_dicts(self, msas, tree):
        '''
        calculate our mapping dicts so we can keep track of things
        (names in MSA files don't necessarily match names in tree file)
        '''
        # assuming we only care about terminals!
        terminals = tree.get_terminals()

        for node in terminals:
            idx = self.find_matching_index(node.name, msas)
            self.node_name_to_index_dict[node.name] = idx
            self.index_to_node_name_dict[idx] = node.name


    def pairwise_identity_value(self, lhs, rhs):
        '''
        Get the pairwise identity value for the given
        MSA identifiers. If these are strings, we assume
        they are MSA names (tho this could be either from
        the tree or the MSA list! be careful). If they are
        ints we assume they are indices into the original
        list of MSAs

        Arguments:
         - lhs: the lhs MSA identifier. This could be the name from the input
                MSA file or the integer index within the MSA file. (Potentially
                could also be the name in the tree file, but this not currently
                supported)
         - rhs: as lhs

        Returns the float identity value for the pair
        '''
        lhs_index = self.find_index(lhs)
        rhs_index = self.find_index(rhs)
        return self.identity_matrix.pairwise_identity_value(lhs_index, rhs_index)

    def find_index(self, identifier):
        '''
        Find the index for the given identifier. If that's a string
        we'll assume (for now) that must be a name from our tree
        (may want to extend so it can find the name from the msa list)
        if it's an int we'll just assume it's the index

        Arguments:
         - identifier: the identifier. An integer id (index in the MSA file), the MSA-space
                       name. We could easily extend to support the Tree-space name as well,
                       but not necessary right now
        '''
        if type(identifier) == int:
            return identifier
        else:
            if identifier not in self.node_name_to_index_dict:
                raise KerfError("Could not find name '%s' in mapping" % identifier)
            return self.node_name_to_index_dict[identifier]

        
    def node_name_from_index(self, idx):
        '''Find the name of the node given the index into our msa sequences'''
        return self.index_to_node_name_dict[idx]

    
    @staticmethod
    def find_matching_index(node_name, msas):
        '''Find the index matching the given node name
        
        Use some name-based matching to link up the names in the tree
        to the ids in the list of MSAs

        Arguments:
         - node_name: the name of the node (in Tree-space)
         - msas: the list of SeqRecord objects
        '''
        # in our example, the node names are split by '_' -- the first bit
        # is the id we want
        base_node_name = node_name.split('_')[0]

        for idx, msa in enumerate(msas):
            # the msa name is a different format -- but there is a part of
            # the id which should match the base node name above
            name_bits = msa.name.split('|')
            if len(name_bits) > 1:
                base_msa_name = name_bits[1]
                if base_node_name == base_msa_name:
                    return idx

        raise KerfError("Could not find matching index for '%s'" % node_name)


def find_node_parent(node, tree):
    '''Get the parent of the given node within the given tree

    Phylo tree doesn't give us direct access to the parent from the node. So we'll
    have to use the tree's root and get the path to the given node, and split that
    returned list of nodes up appropriately

    Arguments:
     - node: The node to get the parent for (a Bio.Phylo.TreeElement node)
     - tree: The tree within which that node lives (a Bio.Phylo.Tree object)

    Returns a Bio.PhyloTreeElement node, or None if we can't find a parent
    '''
    path = tree.root.get_path(node)
    if not path:
        return None
    # path excludes root but includes target (ie node)
    if len(path) == 1: # if it's only 1 that's going to be node itself
        return tree.root
    else:
        return path[-2]

def clean_tree(tree):
    '''Clean the empty clades out of the tree

    Would like to clean up the tree, it's got some empty Clades which i don't think
    should be there. But collapsing/pruning these doesn't seem to be quite working
    as i expect. The first half of this seems to work as expected but printing
    (really draw_ascii) looks weird and getting errors printing some of them, so i
    guess something's wrong there
    '''
    while True:
        found_one = False
        terminals = tree.get_terminals()
        for terminal in terminals:
            if not terminal.name:
                tree.collapse(terminal)
                found_one = True
                continue

        if not found_one:
            break

    #while True:
    #    found_one = False
    #    non_terminals = tree.get_nonterminals()
    #    for clade in non_terminals:
    #        if len(clade.clades) == 1:
    #            tree.collapse(clade)
    #            found_out = True
    #            continue
    #
    #    if not found_one:
    #        break

        
def do_kerf_split(tree, helper, cutoff_value):
    '''Main entry point for the algorithm

    Arguments:
     -tree: the Newick tree to split up (leaves correspond to SeqRecords from first param
     -helper: a KerfHelper instance, used to help us keep the code clean and maintainable
     -cutoff_value: a float to determine cutoff percent identity

    returns a list of subtrees (Phylo.TreeElements)
    '''
    subtrees = []
    processed_nodes = []
    # loop until we're done
    while True:
        node = helper.next_traverse_node(processed_nodes)
        if node is None:
            break
        
        # make a copy of the existing tree (note that 'node' will be in this copy)
        # this should be pretty fast and ensures that our new subtree will preserve
        # traits from the original that we're not tracking (eg branch lengths),
        # plus we'll get most of the structure for free this way
        subtree = copy.deepcopy(tree)
        subtrees.append(subtree)

        added_nodes = []
        visited_nodes = []
        while True:
            finished = _recurse_subtree(tree, subtree, node, added_nodes,
                                        visited_nodes, helper, cutoff_value)
            if finished:
                break

        import pdb
        pdb.set_trace()

        # We've got a bunch of empty clades in the tree, would be nice to clean these out
        # but having some problems with this (Biopython complaining/erroring)
        #clean_tree(subtree)

        processed_nodes.extend(added_nodes)
        
    return subtrees


def _recurse_subtree(tree, subtree, node, added_nodes, visited_nodes, helper, cutoff_value):
    '''recursive method to fill up our subtree by checking all of the nodes in
    the tree and seeing if they qualify'''
    if node in visited_nodes:
        return False

    visited_nodes.append(node)
    
    # we might have a terminal but internal clade, due to us ripping stuff out
    # of our original tree. These nodes won't have names, and we'll treat them as
    # non-terminal (and continue on to parent checking below)
    if node.is_terminal() and node.name:        
        #print "considering node '%s'" % node.name
            
        # if the name is already in our list of added ones, we can break out early
        # (but tell caller to keep searching)
        if node in added_nodes:
            return False
        else:
            if helper.can_add(node, added_nodes, cutoff_value):
                # we keep it. It's already in the subtree, so we just need to
                # mark that we're adding it
                #print "adding '%s' to subtree" % node.name
                added_nodes.append(node)
            else:
                # we can't keep it in our subtree. Remove it from there (it's still
                # in our original tree).

                # note that 'node' isn't really in subtree -- we want to remove the
                # copy that we have in subtree -- we'll match on name
                #print "removing '%s' from candidate tree" % node.name
                # NOTE: don't use prune here! breaks. collapse is what we want anyway
                subtree.collapse(name=node.name)
            
    # if we're not a terminal node, let's check our children
    if not node.is_terminal():
        for clade in node.clades:
            _recurse_subtree(tree, subtree, clade, added_nodes,
                             visited_nodes, helper, cutoff_value)

    parent = find_node_parent(node, tree)
    if not parent:
        return True # finished!

    return _recurse_subtree(tree, subtree, parent, added_nodes,
                            visited_nodes, helper, cutoff_value)


def write_output_files(msas, sub_trees, helper):
    '''write out the output files, as per the spec

    Arguments:
     - msas: list of SeqRecord objects (our input)
     - sub_trees: our generated sub_trees
     - helper: a KerfHelper object we can use for mapping etc
    '''
    output_basename = 'output'
    csv = "%s.csv" % output_basename

    # we'll just do these in cwd
    file_ = open(csv, 'w+')
    
    for idx, msa in enumerate(msas):
        # find which tree this msa lives in (should be only one)
        node_name = helper.node_name_from_index(idx)
        msa_tree_idx = -1
        for tree_idx, tree in enumerate(sub_trees):
            matches = tree.find_clades(name=node_name, terminal=True)
            try:
                matches.next()
            except StopIteration:
                # keep looking
                pass
            else:
                msa_tree_idx = tree_idx
                # found it
                break
        file_.write("%s, %d\n" % (msa.name, msa_tree_idx))

    file_.close()

    write_msa = True
    write_treefile = True
    
    for tree_idx, tree in enumerate(sub_trees):
        if write_msa:
            msa_filename = "%s_subtree_msa_%02d.%s" % (output_basename, tree_idx, MSA_SUFFIX)
            msa_records = []
            terminals = tree.get_terminals()
            for terminal in terminals:
                if terminal.name:
                    idx = helper.find_index(terminal.name)
                    msa_records.append(msas[idx])

            SeqIO.write(msa_records, msa_filename, MSA_FORMAT)

        if write_treefile:
            tree_filename = "%s_subtree_%02d.%s" % (output_basename, tree_idx, OUTPUT_PHYLO_SUFFIX)
            Phylo.write(tree, tree_filename, OUTPUT_PHYLO_FORMAT)

            
def main(args):
    '''
    here we do command line processing, parse files, display output, etc
    '''
    if len(args) < 3:
        raise ArgError("Must supply 3 arguments: msa_file tree_file cutoff_percent")

    # would like to do some more error checking here!
    msa_file = args[0]
    tree_file = args[1]
    cutoff_percent = float(args[2])

    # hardcoded MSA_FORMAT ('fasta') for now
    msa_iter = SeqIO.parse(msa_file, MSA_FORMAT)
    msa_list = list(msa_iter)

    # this could be empty, let's check to make sure it's not
    if not msa_list:
        raise ParseError("No MSAs found in msa file '%s'" % msa_file)

    # Phylo's IO will raise an exception if it's a bad file
    tree = Phylo.read(tree_file, INPUT_PHYLO_FORMAT)

    # the original:
    #Phylo.draw_ascii(tree)
    #print
    #print('-'*80)
    #print

    helper = KerfHelper(msa_list, tree)
    sub_trees = do_kerf_split(tree, helper, cutoff_percent)

    # write the output to named files in the cwd
    write_output = True
    # draw the output to the screen
    draw_output = True

    if write_output:
        write_output_files(msa_list, sub_trees, helper)

    if draw_output:
        print
    
        for sub_tree in sub_trees:
            Phylo.draw_ascii(sub_tree)
            print
            print('-'*80)

            print
            print "%d trees" % len(sub_trees)

    return 0


# if we're called directly
if __name__ == "__main__":
    ret_code = main(sys.argv[1:])
    sys.exit(ret_code)
