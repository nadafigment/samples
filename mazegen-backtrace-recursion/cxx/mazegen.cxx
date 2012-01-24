#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include <string>
#include <bitset>
#include <vector>
#include <utility>

#include <iostream>

// I'm of two minds about using namespace std. It makes the code a lot
// more readable when you're using lots of it. But it can lead to some
// dangerous and hard-to-find errors in real world scenarios
using namespace std;

enum Direction
{
    center,  // we use this for whether we visited it at all
    north,
    south,
    east,
    west,
};

#define NUM_DIRECTIONS 5

typedef bitset<NUM_DIRECTIONS> DirectionField;
typedef vector<Direction> DirectionVector;
typedef vector<vector<DirectionField> > DirectionMatrix;
typedef pair<int, int> IntPair;

void usage(const char *prog)
{
    cerr << "Usage: " << prog << "<width> <height>" << endl;
    cerr << "    width and height must be positive numbers" << endl;
}

/** Return a randomized vector of Directions
    meaning, we always get back the 4 cardinal
    directions, but in some random order */
DirectionVector random_direction_vector()
{
    DirectionVector ordered_vec;
    ordered_vec.push_back(north);
    ordered_vec.push_back(south);
    ordered_vec.push_back(east);
    ordered_vec.push_back(west);

    DirectionVector random_vector;
    // remove items as we go, then find a random index into the remaining,
    // to get a randomized vector
    while (!ordered_vec.empty())
    {
        int rand_index = rand() % ordered_vec.size();
        DirectionVector::iterator iter = ordered_vec.begin() + rand_index;
        random_vector.push_back(*iter);
        ordered_vec.erase(iter);
    }

    return random_vector;
}

/** return the next point, given the direction to go */
IntPair next_point(int x, int y, Direction dir)
{
    switch(dir)
    {
    case north:
        y += 1;
        break;
    case south:
        y -= 1;
        break;
    case east:
        x += 1;
        break;
    case west:
        x -= 1;
        break;
    }

    return IntPair(x, y);
}

/** Opposite direction to the given one */
Direction opposite(Direction dir)
{
    switch(dir)
    {
    case north:
        return south;
    case south:
        return north;
    case east:
        return west;
    case west:
        return east;
    default:
        assert(false);
    }
}

/** can we visit the given cell, considering all the
    points we've visited already.
 
    @param[in]    x    x value of the cell we want to visit
    @param[in]    y    y value of the cell we want to visit
    @param[in]    dim  dimesnions of the grid (IntPair)
    @param[in]    visited a DirectonMatrix, an array of bitfields which indicate if that
                       cell has been visited already
    @return boolean, true if we can visit the cell, false otherwise
*/
bool can_visit_cell(int x, int y, const IntPair &dim, const DirectionMatrix &visited)
{
    if ((x < 0) || (x > dim.first-1) || (y < 0) || (y > dim.second-1))
        return false;
    if (visited[x][y][center])
        return false;
    return true;
}

/** Recurse through the grid. This is the workhorse of the application.
    Given a starting point, randomly check different directions to see if
    we can traverse in that direction. If so, break through that wall and
    recurse to that cell.

    @param[in]    x     x value of the cell we're visiting
    @param[in]    y     y value of the cell we're visiting
    @param[in]    dim   dimention of the grid (IntPair)
    @param[in,out] visited a DirectionMatrix, an array of bitfields which indicate if that
                           cell has been visited already, as well as which walls have been
                           broken
*/
void recurse_maze(int &x, int &y,
                  const IntPair &dim,
                  DirectionMatrix &visited)
{
    DirectionVector direction_vector = random_direction_vector();
    DirectionField &this_field = visited[x][y];
    this_field[center] = 1; // mark that we've visited it

    DirectionVector::iterator iter;
    for (iter = direction_vector.begin(); iter != direction_vector.end(); ++iter)
    {
        IntPair next_pair = next_point(x, y, *iter);
        
        if (can_visit_cell(next_pair.first, next_pair.second, dim, visited))
        {
            DirectionField &next_field = visited[next_pair.first][next_pair.second];
            this_field[*iter] = 1;
            next_field[opposite(*iter)] = 1;
            recurse_maze(next_pair.first, next_pair.second, dim, visited);
        }
    }
}

/** print the matrix. Ascii art, printed to stdout */
void print_matrix(const DirectionMatrix &matrix,
                  const IntPair &start,
                  const IntPair &end,
                  const IntPair &dim)
{
    int x, y, i, j;
    for (y = dim.second-1; y >= 0; y--)
    {
        // we'll have a few rows of text for each
        // row of our grid
        vector<string> rows;
        for (i = 0; i < 5; i++)
            rows.push_back("");
        for (x = 0; x < dim.first; x++)
        {
            DirectionField field = matrix[x][y];

            // only do the left line if we're the first block
            if (x == 0)
            {
                rows[0] += "___";
                rows[1] += " | ";

                if (field[west])
                    rows[2] += "   ";
                else
                    rows[2] += " | ";

                rows[3] += " | ";
                rows[4] += "___";
            }

            if (field[north])
                rows[0] += "   ";
            else
                rows[0] += "___";

            rows[1] += "   ";
            if ((x == start.first) && (y == start.second))
                rows[2] += " O ";
            else if ((x == end.first) && (y == end.second))
                rows[2] += " X ";
            else
                rows[2] += "   ";
            rows[3] += "   ";

            if (field[south])
                rows[4] += "   ";
            else
                rows[4] += "___";

            rows[0] += "___";
            rows[1] += " | ";

            if (field[east])
                rows[2] +=  "   ";
            else
                rows[2] += " | ";

            rows[3] += " | ";
            rows[4] += "___";
        }

        if (y != dim.second-1)
            rows.erase(rows.begin());

        vector<string>::iterator iter;
        for (iter = rows.begin(); iter != rows.end(); ++iter)
        {
            cout << *iter << endl;
        }
        rows.erase(rows.begin(), rows.end());
    }
}

/** initialize the matrix with DiretionFields */
void init_matrix(DirectionMatrix &matrix, const IntPair &dim)
{
    int i, j;
    for (i = 0; i < dim.first; i++)
    {
        vector<DirectionField> row;
        for (j = 0; j < dim.second; j++)
        {
            row.push_back(DirectionField());
        }
        matrix.push_back(row);
    }
}

int main (int argc, char *argv[])
{
    if (argc < 3)
    {
        usage(argv[0]);
        return 1;
    }

    const int width = atoi(argv[1]);
    const int height = atoi(argv[2]);

    if ((width == 0) || (height == 0)) {
        usage(argv[0]);
        return 2;
    }
    
    IntPair dim(width, height);

    // initialize random seed:
    srand(time(NULL));

    // We'll keep track of where we've been and what walls we've
    // broken through with this matrix
    DirectionMatrix visited;
    init_matrix(visited, dim);

    IntPair start_point(0, 0); // user always starts at lower right
    IntPair end_point(rand() % width, rand() % height); // random end point

    // The guts of it all
    recurse_maze(end_point.first, end_point.second, dim, visited);

    // print it to stdout.
    print_matrix(visited, start_point, end_point, dim);
    
    return 0;    
}
