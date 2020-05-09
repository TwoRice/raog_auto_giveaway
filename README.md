## RAOG Auto Giveaway
A collection of scripts to help automate giveaways on [reddit.com/r/RandomActsOfGaming](https://www.reddit.com/r/RandomActsOfGaming).

There are currently two scripts in this repo
1. winner_selector
2. pm_winners

### Prerequisites & Setup
Python 3 ([Install Guide](https://realpython.com/installing-python/))

PIP ([Install Guide](https://pip.pypa.io/en/stable/installing/))

This step is only nessessary to use the PM winners script.

Create a config file with details for a reddit app, details on how to do this below:
1. While logged in to reddit go to https://www.reddit.com/prefs/apps/
2. Click "create another app..."
3. Enter any name, select script, enter http://localhost:8080 into redirect url
3. Click create app
4. Copy client id, the client id is found under the app's name, it is a 14 character long string.
5. Copy client secret, it should be listed as "secret" if you do see this, click edit on your app, and it should come up
6. copy these details along with your reddit username and password into a file named congif.ini
```
[redditapp]
client_id=YOUR_CLIENT_ID
client_secret=YOUR_CLIENT_SECRET
username=YOUR_USERNAME
password=YOUR_PASSWORD
```

Run ```pip install -r requirements.txt``` to install nessessary packages to run scripts

Instructions on using each of these scripts follow below:

### Winner Selector
This script handles the winner selection stage, and selects winners from the comments for each game to be given away.
**Note:** Please ensure users enter the name of the game you are giving away exactly as you have it in your list of games otherwise the script will not find their entry

#### Agruments & Options
Arguments (required): 
1. post_id - The 6 character reddit post id for the giveaway eg.
For reddit post url - reddit.com/r/RandomActsOfGaming/comments/fvwo50/50_humble_bundle_game_giveaway/ the post id is fvwo50
2. game_list_path - path to csv file (a txt file will work too as long as its formatted like a csv) containing list of keys, and optionally the keys for the games, if you want to automate giving out the keys include the game keys in this file. The file should be formatted as below:
```
Hollow Knight, ABC123
Two Point Hospital, DEF456
Enter the Gungeon, GHI789
```
3. num_choices - the number of games a user is allowed to enter the giveaway for, if a user lists more game names than num_choices the extra choices will just be ignored.
4. out_path - the path for the output csv file eg. game_winners.csv

#### How it works:
1. Users comment on the giveaway post with an ordered list of games they would like to win eg.
```
Entering giveaway for
Hollow Knight
Two Point Hospital 
Enter the Gungeon
```
2. For each game in the list, the script looks for all comments which list this game as their top/#1 choice, a winner is then randomly selected from this pool of users. If no users specified the game as their top/#1 choice, then the script looks for all users who specified the game as their 2nd choice and so on.
3. Once all winners have been chosen the script outputs a csv file of the winners for each game, along the with game keys (if specified in the game list). This is used as the input to the pm_winners script.

#### Usage Examples
```
python winner_selector.py fvwo50 game_list.csv 3 game_winners.csv
```

#### Known Limitations
* Games which contain the entire name of another game as the start of their name must be listed after the other game in your game list eg. If you are giving away Cities in Motion and Cities in Motion 2, Cities in Montion must come first in your game list, the easiest way to achieve this is to sort your game list into alphabetical order
* May choose the same winner multiple times for 1 game for have multiple copies of the same game
* Allows users to win multiple games - some giveaway operaters may want to limit their giveaway be more "fair" by only allowing users to win one game.

### PM Winners
This scripts handles sending private messages to all the winners, letting them know they have won/sending them the keys for the games they have won.

### Arguments & Options
Arguments (required):
1. winners_file - The output of the winner_selector script: path to the csv file (a txt file will work too as long as its formatted like a csv) containing the winners for each game and optionally the game keys. The file should be formatted as below:
```
Hollow Knight, bob, ABC123
Two Point Hospital, mary, DEF456
Enter the Gungeon, jane, GHI789
```

Options (Optional):
* -C, --config_file 
    * Default: config.ini 
    * path to config file containing nessessary details to connect to reddit app - client id, client secret, your reddit username, your reddit password (refer to the Prerequisites section, to understand how to get these details)
* -S, --subject_template 
    * Default: You won GAME 
    * subject template for PM sent to each winner use keywords USER GAME and KEY (in caps) to act as placeholders for the winners username, the game name and the game key
* -B, --body_template 
    * Default: Hey USER you won GAME in my giveaway, here is your key: KEY 
    * body template for PM sent to each winner use keywords USER GAME and KEY (in caps) to act as placeholders for the winners username, the game name and the game key
* -S, --message-sleep
    * Default: 0.1
    * Number of seconds to wait between sending each message

### Usage Examples
Default
```
python pm_winners game_winners.csv
```
Using a custom named config file
```
python pm_winners game_winners.csv -C my_config.ini
```
Adding a 2 second wait time between each message
```
python pm_winners game_winners.csv -M 2
``` 
Using a custom message
```
python pm_winners game_winners.csv -S Hello USER you won in my giveaway! -B You won GAME, here's the game key KEY
```

### Known Limitations
* If you reddit account is not sufficiently old or does not have enough karma, you will not be able to mass private message users using a script, and this script likely will not work as intended
