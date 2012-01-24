// A simple program that computes the square root of a number
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include <iostream>
#include <fstream>

#include <ctime>
#include <time.h>

#include <string>
#include <list>

#include <algorithm>

#include "word.h"

// I'm of two minds about using namespace std. It makes the code a lot
// more readable when you're using lots of it. But it can lead to some
// dangerous and hard-to-find errors in real world scenarios
using namespace std;

void free_words(WordList &words)
{
    WordList::iterator iter;
    for (iter = words.begin(); iter != words.end(); ++iter)
    {
        delete *iter;
    }
}

int main (int argc, char *argv[])
{
    /*
    Word a("cat");
    Word b("bat");
    Word c("feek");
    Word d("gap");

    cout << a.levenshtein_distance(b) << endl;
    cout << b.levenshtein_distance(c) << endl;
    cout << a.levenshtein_distance(d) << endl;
    */
    
    if (argc < 2)
    {
        fprintf(stdout, "Usage: %s <word_to_check <wordfile>\n",
                argv[0]);
        return 1;
    }

    string word_to_check(argv[1]);

    string line;
    Word *start_word = NULL;
    WordList all_words;

    ifstream wordfile(argv[2]);
    if (wordfile.is_open())
    {
        while (wordfile.good())
        {
            getline(wordfile, line);
            line.erase(remove(line.begin(), line.end(), '\n'), line.end());
            if (!line.empty())
            {
                Word *word = new Word(line);
                if (line == argv[1])
                    start_word = word;
                all_words.push_back(word);
            }
        }
    }

    if (!start_word)
    {
        cerr << "Could not find '" << argv[1] << "' in word list file!" << endl;
        free_words(all_words);
        return 2;
    }

    int start_time = clock();

    StringSet network;

    bool preprocess_all_words = false;

    if (preprocess_all_words)
    {
        WordList::iterator iter;
        for (iter = all_words.begin(); iter != all_words.end(); ++iter)
        {
            (*iter)->build_friend_network(all_words);
        }

        start_word->fill_network(network);
    }
    else
    {
        start_word->generate_social_network(network, all_words);
    }


    //start_word.generate_social_network(network, all_words);
    cout << "Size is: " << network.size() << endl;


    // pass in reference to that 'network' list as a reference
    // it's going to get quite large, we don't want to copy it
    //build_network(start_word, all_words);

    int elapsed_ticks = clock() - start_time;
    float elapsed_secs = elapsed_ticks / (float) CLOCKS_PER_SEC;
    cout << "(Full processing took " << elapsed_secs << " secs)" << endl;

    //print "social network of '%s' (inclusive) consists of %d unique words" \
    //    % (start_word.word, len(network_set))

    free_words(all_words);
    
    return 0;
}
