import praw
import click
import pandas as pd

from tqdm import tqdm
from time import sleep
from configparser import ConfigParser

#OAuth imports:
from OAuthTokenRetrieval import send_message, receive_connection
import random

"""
Connects to a reddit app through PRAW

Args:
    config_file: str - path to config file containing details to connect to reddit app
"""
def _connect_to_reddit(config_file):
    config = ConfigParser()
    config.read(config_file)
    client_id = config.get('redditapp', 'client_id')
    client_secret = config.get('redditapp', 'client_secret')
    #username = config.get('redditapp', 'username')
    #password = config.get('redditapp', 'password')
    redirect_uri = config.get('redditapp', 'redirect_uri')

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        #username=username,
        #password=password,
        user_agent='giveawayscript/pm_winners/script',
        redirect_uri = redirect_uri
    )

    # OAuth here:
    state = str(random.randint(0, 65000))
    url = reddit.auth.url(["identity", "privatemessages"], state, "permanent")
    print("Now open this url in your browser: " + url)

    client = receive_connection()
    data = client.recv(1024).decode("utf-8")
    param_tokens = data.split(" ", 2)[1].split("?", 1)[1].split("&")
    params = {
        key: value
        for (key, value) in [token.split("=") for token in param_tokens]
    }
    reddit.auth.authorize(params["code"])

    return reddit

"""
Generates a messages from a template replacing placeholders with winner's username, the game titel
and the game key

Args:
    message: str - message template

Kwargs:
    user: str (default=None) - username of the winner
    game: str (default=None) - title of the game
    key: str (default=None) - game key
"""
def _gen_message(message, user=None, game=None, key=None):
    if user:
        message = message.replace('USER', user)
    if game:
        message = message.replace('GAME', game)
    if key:
        message = message.replace('KEY', key)

    return message

@click.command()
@click.argument('winners_file', nargs=1)
@click.option('-C', '--config_file', default='config.ini', help='path to config file containing nessessary details to connect to reddit app - client id, client secret, your reddit username, your reddit password')
@click.option('-B', '--subject_template', default='You won GAME', help='Subject template for PM sent to each winner use keywords USER GAME and KEY (in caps) to act as placeholders for the winners username, the game name and the game key')
@click.option('-B', '--body_template', default='Hey USER, you won GAME in my giveaway, here is the key: KEY', help='Body template for PM sent to each winner use keywords USER GAME and KEY (in caps) to act as placeholders for the winners username, the game name and the game key')
@click.option('-S', '--message-sleep', default=0.1, help='Number of seconds to wait between sending each message')
def pm_winners(winners_file, config_file, subject_template, body_template, message_sleep):
    """
    Given a csv of each game's winner and game key, PMs each winner to let them know they have won, along with the game's key
    """
    reddit = _connect_to_reddit(config_file)
    winners = pd.read_csv(winners_file, names=['game', 'winner', 'key'], index_col='game')
    for game, winner in tqdm(winners.iterrows()):
        message_subject = _gen_message(subject_template, game=game)
        message_body = _gen_message(body_template, user=winner.winner, game=game, key=winner.key)
        reddit.redditor(winner.winner).message(message_subject, message_body)
        sleep(message_sleep)

if __name__ == '__main__':
    pm_winners()
