#pragma once

#include <string>
#include <vector>
#include <set>
#include <queue>

#include <ostream>

// forward declare for typedef
class Word;

typedef std::vector<Word*> WordList;
typedef std::vector<std::string> StringList;
typedef std::set<std::string> StringSet;
typedef std::queue<Word*> WordQueue;

class Word
{
  public:
    Word();
    Word(const std::string &);
    ~Word();

    int levenshtein_distance(const Word &word);

    void build_friend_network(WordList &words);

    bool can_be_friends_with(const Word &word);

    void add_friend(Word *word);

    void fill_network(StringSet &network);

    void generate_social_network(StringSet &network, WordList &all_words);

    const char *word() const { return m_word.c_str(); }
    bool empty() const { return m_word.empty(); }

    friend std::ostream &operator<<(std::ostream &os, const Word &word);

  private:
    std::string m_word;
    WordList m_friends;
    StringSet m_friend_names;
    bool m_built_network;
};
