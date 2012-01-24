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

void Word::build_friend_network(WordList &words)
{
    /*
      build our network of friends, given the list of the entire population

      param all_words: the entire word population known to us
      type all_words: list of FriendlyWord objects

      return: None
    */

    if (!m_built_network)
    {       
        cout << "building network for '" << m_word << "'" << endl;
        WordList::iterator iter;
        for (iter = words.begin(); iter != words.end(); ++iter)
        {
            if (can_be_friends_with(*iter))
                add_friend(*iter);

            m_built_network = true;
        }
    }
}

void Word::add_friend(Word &word)
{
    m_friends.push_back(word);
    // this is a symmetrical relationship, no?
    word.add_friend(*this);
}

bool Word::can_be_friends_with(const Word &word)
{
    if (levenshtein_distance(word) == 1)
    {
        cout << "<" << *this << ">, <" << word << ">" << endl;       
        return true;
    }
    else
        return false;
}

int Word::levenshtein_distance(const Word &word)
{
    //if (word.m_word.length() != m_word.length())
    //    return 0;

    //if (word.m_word == m_word)
    //    return 0;

    // i don't really like using non-descriptive variable names
    // like 'm' but this is coming straight from the ref at wikipedia
    const int m = m_word.length();
    const int n = word.m_word.length();

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

void Word::generate_social_network(StringSet &network_set, WordList &all_words)
{
    /*
      the main entry point for building a FriendlyWord's social network
      
      Note: this will be slow! O(n^2) in worst case (where n is length of all_words)
    */
    // add ourself
    network_set.insert(m_word);

    //assume that we haven't built our network already. There are checks in that
    // method to make sure it doesn't run numerous times, but the way we've structured
    // things here (checking if friends are already in the set before recursing) this
    // shouldn't ever happen
    build_friend_network(all_words);

    WordList::iterator iter;
    for (iter = m_friends.begin(); iter != m_friends.end(); ++iter)
    {
        cout << "checking out " << *iter << endl;
        if (network_set.find((*iter).m_word) != network_set.end())
            (*iter).generate_social_network(network_set, all_words);
    }
}
