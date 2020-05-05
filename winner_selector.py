import re
import csv
import math
import click
import psraw
import string
import requests
import pandas as pd

from random import choice
from datetime import datetime

_remove_punc_pattern = re.compile('[\W_]+')

"""
Get users with the specified game as their nth choice

Args:
    user games: dict -

    game: string - game to search for

    n: int - position in the user's game list to search in
"""
def _user_game_search(user_games, game, n):
    return [user for user, games in user_games.items() if len(games) > n and games[n] == game]

"""
Replace all non-alphanumeric characters in a string with a space
and collapse multiple spaces into one

Args:
    s: string - input string
"""
def _remove_punc(s):
    "replace punctuation with a space"
    s = _remove_punc_pattern.sub(' ', s)
    "collapse multiple spaces into one"
    s = re.sub(' +', ' ', s)
    return s

"""
Generates a pushshift url to retrieve comments from a reddit post before a given time

Args:
    post_id: str - 6 character reddit post id
    timestamp: int - timestamp of datetime to pull comments before, used for pagination
"""
def _gen_pushshift_url(post_id, timestamp):
    return 'https://api.pushshift.io/reddit/comment/search/?link_id={}&limit=1000&before={}'.format(post_id, timestamp)

"""
Opens game list file and extracts game names and game keys if supplied

Args:
    game_list_path: str - path to csv or txt file containing list of games
"""
def _get_game_list(game_list_path):
    game_list = pd.read_csv(game_list_path, header=None)
    num_columns = len(game_list.columns)

    if num_columns > 2:
        raise ValueError('Game list file should have a maximum of 2 columns (game names and game keys)')
    elif num_columns == 2:
        game_list.columns = ['game', 'key']
        missing_keys = game_list[(game_list.key.isna()) | (game_list.key == ' ') | (game_list.key == '')]
        if len(missing_keys) > 0:
            print('WARNING: Games missing keys:')
            print(missing_keys.game.values)
            print()
    else:
        game_list.columns = ['game']

    game_list['game'] = game_list.game.apply(lambda game: _remove_punc(game).lower())
    game_list.set_index('game', inplace=True)

    # Hacky fix for being able to find games which names contain entire other game names at the start of theirs
    # eg. Cities in Motion & Cities in Motion 2. if we assume the game_list is passed in in alphabetical order,
    # this "fixes" that issue.
    game_list = game_list.iloc[::-1]

    return game_list

"""
Fetches comments from giveawya post and removes all delted and child comments

Args:
    post id: str - 6 character post_id for giveaway, found in the url
"""
def _retrieve_comments(post_id):
    all_comments = []
    previous_epoch = int(datetime.utcnow().timestamp())
    while True:
        pushshift_endpoint = _gen_pushshift_url(post_id, previous_epoch)
        response = requests.get(pushshift_endpoint).json()
        if 'data' in response and len(response['data']) > 0:
            data = response['data']
            all_comments.extend(data)
            previous_epoch = data[-1]['created_utc']
        else:
            break

    print('Retrieved {} comments'.format(len(all_comments)))
    comments = [comment for comment in all_comments if comment['body'] != '[removed]' and comment['body'] != '[deleted]']
    comments = [comment for comment in comments if comment['parent_id'][:3] == 't3_']
    print('Removed {} deleted and child comments\n'.format(len(all_comments) - len(comments)))

    return comments

"""
Extracts the choices from the users' entries

Args:
    comments: list - list of comments from the giveaway post
    game_list: list(str) - list of games in the giveaway
"""
def _extract_user_choices(comments, game_list):
    game_regex = r'\b(?:' + '|'.join(game_list.index) + r')\b'
    user_games = {
        comment['author']: re.findall(game_regex, _remove_punc(comment['body'].lower()))
        for comment in comments
    }

    return user_games

"""
Selects 1 winner for each game

Args:
    user_games: dict - map of users and the games they have entered to win
    game_list: list(str) - list of games in the giveaway
    num_choices: int - the maximum number of games a user can enter to win
"""
def _select_winners(user_games, game_list, num_choices):
    game_winners = {}
    for game in game_list.index:
        nominees = None
        for i in range(num_choices):
            nominees = _user_game_search(user_games, game, i)
            if nominees: break

        if nominees:
            game_list.loc[game, 'winner'] = choice(nominees)
    leftover_games = game_list[game_list.winner.isna()]

    if len(leftover_games) > 0:
        print('No winners chosen/found for games:')
        print(leftover_games.index.values)
        print()

    return game_list

"""
Save the winner for each game to a csv

Args:
    game_winners: dict - map of games to the winners
    out_path: - path to csv file to save results to
"""
def _save_results(game_winners, out_path):
    with open(out_path, 'w') as f:
        writer = csv.writer(f)
        for game, row in game_winners.iterrows():
            if type(row.winner) != float:
                if 'key' in game_winners:
                    writer.writerow((game, row.winner, row.key))
                else:
                    writer.writerow((game, row.winner))

@click.command()
@click.argument('post_id', nargs=1)
@click.argument('game_list_path', nargs=1)
@click.argument('num_choices', nargs=1, type=int)
@click.argument('out_path', nargs=1)
def choose_winners(post_id, game_list_path, num_choices, out_path):
    """
    Given a reddit giveaway post and a list of games to giveaway chooses winners for each game from the comments.

    Args:
        post_id: str - 6 character reddit post id for the giveaway.
        game_list_path: str - path to csv of the list of games in the giveaway.
        num_choices: int - number of games a single user can enter the giveaway to win.
        out_path: str - path for the output csv to save the winners to.
    """
    game_list = _get_game_list(game_list_path)
    comments = _retrieve_comments(post_id)
    user_games = _extract_user_choices(comments, game_list)
    game_winners = _select_winners(user_games, game_list, num_choices)
    _save_results(game_winners, out_path)

if __name__ == '__main__':
    choose_winners()
