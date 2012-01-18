#!/usr/bin/env python
# importing from the FUTURE!! Developed under 2.5, which only contains 'with'
# when you specify this magical import. Could get around the with easily, but
# makes the code look nicer below
from __future__ import with_statement

import sys
import time
# see some comments below -- i like debuggers, even for high-level script-y
# languages like python
#import pdb

# don't like magic constants in code, prefer to put them as what i call #defines
# (my legacy of C++) at the beginning of modules
RECURSION_LIMIT = 10000 # python 2.5's default of 1000 not cutting it for
# our big ol' word file

class FriendlyWord(object):
    '''
    Class which represents a word which can have some friends
    '''

    def __init__(self, word):
        self.word = word
        self.friends = []
        self.built_network = False

    def build_friend_network(self, all_words):
        '''
        build our network of friends, given the list of the entire population

        param all_words: the entire word population known to us
        type all_words: list of FriendlyWord objects

        return: None
        '''
        # This is the only method i've "properly" documented, to show that i care
        # about such things. That's roughly epydoc format from memory. I'm doing this
        # whole thing rather quickly, as you're not paying me and i've got some other
        # stuff i should be doing. But i do feel pretty strongly about docs and
        # comments, and for code that's going to live for any length of time and/or be
        # used by anyone else, i feel like there should be time scheduled to write docs
        # and strong emphasis on them being there (eg done conditions not satisfied, or
        # code review fails)

        #we cache whether we've built that already, to make sure we don't do it
        #multiply. But note that this assumes our population hasn't changed from when
        # we got built! This could be cleaned up if we wanted to be a bit more careful
        # about that
        if not self.built_network:
            
            # don't like leaving stuff like this in code, but again lets you see some
            # of how i code etc. I tend to prefer using a debugger (pdb for python) to
            # step thru code as opposed to putting prints all over. But that can be somewhat
            # painful with recursive methods. So i threw this in here to make sure everything
            # looked kosher as i went
            #print "building network for '%s'" % self.word

            for word in all_words:
                if self.can_be_friends_with(word):
                    self.friends.append(word)

            self.built_network = True

    def can_be_friends_with(self, word):
        # Separate out the logic for determining if words can be friends into this
        # separate method; seems like a criteria that might change down the line
        if has_levenshtein_distance_of_one(self.word, word.word):
            return True
        return False

    def generate_social_network(self, network_set, all_words):
        '''
        the main entry point for building a FriendlyWord's social network

        Note: this will be slow! O(n^2) in worst case (where n is length of all_words)
        '''
        # add ourself
        network_set.add(self.word)

        # assume that we haven't built our network already. There are checks in that
        # method to make sure it doesn't run numerous times, but the way we've structured
        # things here (checking if friends are already in the set before recursing) this
        # shouldn't ever happen
        self.build_friend_network(all_words)

        for friend in self.friends:
            if friend.word not in network_set:
                friend.generate_social_network(network_set, all_words)
                


def has_levenshtein_distance_of_one(lhs_word, rhs_word):
    '''
    not that we like to cheat so much, but our problem states that a word's frends
    have levenshtein distance of 1. So in fact we just want to know if words are 1
    unit apart or not; we can more quickly and easily check that than calculate the
    full levenshtein distance. See 
      http://en.wikipedia.org/wiki/Levenshtein_distance
    For completeness and better extensibility would be good to have a func that
    returns the distance
    '''
    # lengths don't match, bail
    if len(lhs_word) != len(rhs_word):
        return False

    # this would be l-distance of 0, bail
    if lhs_word == rhs_word:
        return False

    mismatches = 0
    for i in xrange(len(lhs_word)):
        if lhs_word[i] != rhs_word[i]:
            mismatches = mismatches + 1

        # bail out
        if mismatches > 1:
            return False

    if mismatches == 1:
        return True

    return False


def main(args):
    sys.setrecursionlimit(RECURSION_LIMIT)
    
    if len(args) != 3:
        print "usage %s <word_to_check> <wordfile>" % args[0]
        return 1

    word_to_check = args[1]
    wordfile = args[2]

    start_word = None
    all_words = []
    with open(wordfile) as file_:
        for line in file_:
            line = line.strip() # newlines, any whitespace
            word = FriendlyWord(line)
            all_words.append(word)
            if word.word == word_to_check:
                start_word = word

    if not start_word:
        print "Could not find '%s' in list file ('%s')" % (word_to_check, wordfile)
        return 2
    
    start = time.time()

    # leaving these lines in for you to see thought processes. Had a feeling this
    # brute force approach wouldn't be ideal, but thought it's simplest way
    # rapidly saw that this approach would take days
    #for word in all_words[:20]:
    #    print "building network for '%s'" % word.word
    #    word.build_friend_network(all_words)

    # modified brute force a bit to just start at the one we care about and
    # only build network if we need to. We pass a set which holds the network
    # we'll check this set at the end to see our results, but also provides a
    # convenient way of not recursing into words we've already checked
    network_set = set()
    start_word.generate_social_network(network_set, all_words)

    elapsed = time.time() - start
    #print "(Full processing took %f secs)" % elapsed
    #print '-'*80

    print "social network of '%s' (inclusive) consists of %d unique words" \
        % (start_word.word, len(network_set))

    return 0


if __name__ == '__main__':
    # leaving these in here to show you thought processes etc --
    # i like TDD for some stuff, this (slightly cheesy) func is the
    # core of building that social network
    #print has_levenshtein_distance_of_one('fee', 'foo')
    #print has_levenshtein_distance_of_one('goat', 'boat')
    #print has_levenshtein_distance_of_one('fee', 'goat')
    #print has_levenshtein_distance_of_one('super', '')

    sys.exit(main(sys.argv))
