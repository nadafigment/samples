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

bool Word::can_be_friends_with(const Word &word)
{
    if (levenshtein_distance(word) == 1)
        return true;
    else
        return false;
}

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

int Word::levenshtein_distance(const Word &word)
{
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
    WordQueue queue;

    queue.push(this);
    Word *word;
    
    while (!queue.empty())
    {
        word = queue.front();
        queue.pop();
        word->build_friend_network(all_words);

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
