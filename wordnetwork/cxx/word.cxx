// The word class implementation

#include <iostream>
#include <fstream>

#include <ctime>
#include <time.h>

#include <algorithm>

#include "word.h"

// I'm of two minds about using namespace std. It makes the code a lot
// more readable when you're using lots of it. But it can lead to some
// dangerous and hard-to-find errors in real world scenarios
using namespace std;

int min3(int x, int y, int z)
{
    return min(x, min(y, z));
}

ostream& operator<<(ostream& os, const Word& word)
{
    os << word.m_word.c_str();
    return os;
}


Word::Word()
:     m_built_network(false)
{
}

Word::Word(const string &word)
:     m_word(word),
      m_built_network(false)
{
}

Word::~Word()
{
}

/** build our network of friends, given the list of the entire population

    By our spec, a word can be another word's friend if their levenshtein_distance
    from one another is 1. That distance is a symmetrical property, so we'll
    go ahead and add ourself to the other word's network at the same time to shortcut
    in case that needs to happen later. This is a safe thing to do, and smells right.

    @param[in,out] words  all of the words in the system
    @return None
*/
void Word::build_friend_network(WordList &words)
{
    if (!m_built_network)
    {
        WordList::iterator iter;
        for (iter = words.begin(); iter != words.end(); ++iter)
        {
            if (can_be_friends_with(**iter))
                add_friend(*iter);
        }

        m_built_network = true;
    }
}

void Word::add_friend(Word *word)
{
    if (m_friend_names.find(word->m_word) == m_friend_names.end())
    {
        m_friends.push_back(word);
        m_friend_names.insert(word->m_word);

        // this is a symmetrical relationship, no?
        // add it other direction. We don't really want to call add_friend on
        // that other word as it'll slow us down, though would be more elegant
        word->m_friends.push_back(this);
        word->m_friend_names.insert(m_word);
    }
}

/** Two words can be friends iff their levenshtein_distance is 1 */
bool Word::can_be_friends_with(const Word &word)
{
    if (levenshtein_distance(word) == 1)
        return true;
    else
        return false;
}

/** Walk through our entire network -- meaning our friends and our friends' friends
    and those friends' friends' friends, etc  */
void Word::fill_network(StringSet &network)
{
    network.insert(m_word);
    
    WordList::iterator iter;
    for (iter = m_friends.begin(); iter != m_friends.end(); ++iter)
    {
        if (network.find((*iter)->m_word) == network.end())
        {
            (*iter)->fill_network(network);
        }
    }
}

/** Compute the Levenshtein distance between this word and the
    given one.

    See
    http://en.wikipedia.org/wiki/Levenshtein_distance
    for details, and in fact i've directly ported that straight
    from the article there.
*/
int Word::levenshtein_distance(const Word &word)
{
    const int m = m_word.length();
    const int n = word.m_word.length();

    // This was a simplification which i had made in the python version, which in
    // fact is not correct according to the wikipedia implementation! 
    //if (m != n)
    //    return 0;

    // not crazy about these variable names, but this is coming straight
    // from wikipedia.
    int d[m+1][n+1];

    int i, j;
    for (i = 0; i <= m; i++)
        d[i][0] = i;
    for (j = 0; j <= n; j++)
        d[0][j] = j;

    for (j = 1; j <= n; j++)
    {
        for (i = 1; i <= m; i++)
        {
            if (m_word[i-1] == word.m_word[j-1])
                d[i][j] = d[i-1][j-1];
            else
                d[i][j] = min3(d[i-1][j]+1,
                               d[i][j-1]+1,
                               d[i-1][j-1]+1);
        }
    }

    return d[m][n];
}

/** generate the social network for this word. We fill up network_set as we
    go, all the while using the 'master list' of all_words to use as our
    population.

    Using this lazy method, of only generating networks when we need them
    will result in a lot fewer calculations. But we're still O(n^2) in the
    worst case
*/
void Word::generate_social_network(StringSet &network_set, WordList &all_words)
{
    // We could recurse. But instead we'll use this queue and iterate everywhere.
    // with really big input sets, we'd run out of stack space too quickly with the
    // recursion method
    WordQueue queue;

    queue.push(this);
    Word *word;
    
    while (!queue.empty())
    {
        word = queue.front();
        queue.pop();
        word->build_friend_network(all_words);
           
        //std::cout << "Building network for '" << word->m_word << "': " << network_set.size() << endl;

        if (network_set.find(word->m_word) == network_set.end())
        {
            network_set.insert(word->m_word);

            WordList::iterator iter;
            for (iter = word->m_friends.begin(); iter != word->m_friends.end(); ++iter)
            {
                queue.push(*iter);
            }
        }
    }
}
