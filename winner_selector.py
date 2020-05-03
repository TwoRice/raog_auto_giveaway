import re
import csv
import click
import psraw
import string
import requests

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

def _gen_pushshift_url(post_id, timestamp):
    return 'https://api.pushshift.io/reddit/comment/search/?link_id={}&limit=1000&before={}'.format(post_id, timestamp)

"""
Opens game list file and extracts game names and game keys if supplied

Args:
    game_list_path: str - path to csv or txt file containing list of games
"""
def _get_game_list(game_list_path):
    with open(game_list_path, 'r') as f:
        reader = csv.reader(f)
        game_list_file_contents = list(reader)
    columns = list(map(list, zip(*game_list_file_contents)))

    game_keys = None
    game_list = columns[0] 
    game_list = [_remove_punc(g.lower()) for g in game_list]
    if len(columns) == 2:
        game_keys = dict(game_list_file_contents) 
    elif len(columns) > 2:
        raise ValueError('Game list file should have a maximum of 2 columns (game names and game keys)')
    return game_list, game_keys

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
    print('Removed {} deleted and child comments'.format(len(all_comments) - len(comments)))

    return comments

"""
Extracts the choices from the users' entries

Args: 
    comments: list - list of comments from the giveaway post
    game_list: list(str) - list of games in the giveaway
"""
def _extract_user_choices(comments, game_list):
    game_regex = r'\b(?:' + '|'.join(game_list) + r')\b'
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
    for game in game_list:
        nominees = None
        for i in range(num_choices):
            nominees = _user_game_search(user_games, game, i)
            if nominees: break

        if nominees:
            game_winners[game] = choice(nominees)

    return game_winners

"""
Save the winner for each game to a csv

Args:
    game_winners: dict - map of games to the winners
    out_path: - path to csv file to save results to
"""
def _save_results(game_winners, game_keys, out_path):
    if game_keys:
        results = [(game, winner, game_keys[game]) for game, winner in game_winners.items()]
    else:
        results = [(game, winner) for game, winner in game_winners.items()]

    with open(out_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(results)

@click.command()
@click.argument('post_id', nargs=1) 
@click.argument('game_list_path', nargs=1) 
@click.argument('num_choices', nargs=1, type=int) 
@click.argument('out_path', nargs=1) 
def choose_winners(post_id, game_list_path, num_choices, out_path):
    game_list, game_keys = _get_game_list(game_list_path)
    comments = _retrieve_comments(post_id)
    user_games = _extract_user_choices(comments, game_list)
    game_winners = _select_winners(user_games, game_list, num_choices)
    _save_results(game_winners, game_keys, out_path)

if __name__ == '__main__':
    choose_winners()
