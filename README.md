# Rock Paper Scissors with Google App Engine

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
Deploy your application.



## Game Description:
Rock Paper Scissors is a simple game. Each game consists of a number of rounds.
This is the `best_of` field, which defaults to 3, but can be set to any odd number.
Each round of the match consists of a specified `player_move`, which can only be the stringsRock, Paper, or Scissors.
The player's moves are sent to the `make_move` endpoint which will reply with the updated game state.
The game standings are tracked in the `player_wins` and `computer_wins` field and the game will proceed until
either has won enough rounds to win the whole game.
Many different games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter `urlsafe_game_key`.

## Files Included:
- api.py: Contains endpoints and game playing logic.
- app.yaml: App configuration.
- cron.yaml: Cronjob configuration.
- main.py: Handler for taskqueue handler.
- models.py: Entity and message definitions including helper methods.
- utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

## Endpoints Included:
- **create_user**
	- Path: 'user'
	- Method: POST
	- Parameters: user_name, email (optional)
	- Returns: Message confirming creation of the User.
	- Description: Creates a new User. user_name provided must be unique. Will 
	raise a ConflictException if a User with that user_name already exists.

- **new_game**
	- Path: 'game'
	- Method: POST
	- Parameters: user_name, best_of (optional)
	- Returns: GameForm with initial game state.
	- Description: Creates a new Game. user_name provided must correspond to an
	existing user - will raise a NotFoundException if not. best_of must be a valid
	odd number greater than zero, if not provided it will default to 3.

- **get_game**
	- Path: 'game/{urlsafe_game_key}'
	- Method: GET
	- Parameters: urlsafe_game_key
	- Returns: GameForm with current game state.
	- Description: Returns the current state of a game.

- **get_game_history**
	- Path: 'history/{urlsafe_game_key}'
	- Method: GET
	- Parameters: urlsafe_game_key
	- Returns: StringMessages that show the history of moves played in the game
	- Description: Will return a list of moves played for the game specified by the game key.
	Each element of the list is a string that contains the player move and computer seperated by
	1 comma and 1 space.

- **cancel_game**
	- Path: 'game/{urlsafe_game_key}'
	- Method: DELETE
	- Parameters: urlsafe_game_key
	- Returns: StringMessage confirming succesful deletion
	- Description: Removes the game specified by the given key from the database

- **make_move**
	- Path: 'game/{urlsafe_game_key}'
	- Method: PUT
	- Parameters: urlsafe_game_key, move
	- Returns: GameForm with new game state.
	- Description: Accepts a 'move' and returns the updated state of the game.
	A move must either be the String "Rock", "Paper", or "Scissors", no action will be taken on invalid moves.
	If this causes a game to end, a corresponding Score entity will be created.

- **get_scores**
	- Path: 'scores'
	- Method: GET
	- Parameters: None
	- Returns: ScoreForms.
	- Description: Returns all Scores in the database (unordered).

- **get_user_rankings**
	- Path: 'rankings'
	- Method: GET
	- Parameters: None
	- Returns: PerformanceForms.
	- Description: Calculates a PerformanceForm for ever User in the database (their name and winrate among all finished games).
	Returns all the PerformanceForms.

- **get_user_scores**
	- Path: 'scores/user/{user_name}'
	- Method: GET
	- Parameters: user_name
	- Returns: ScoreForms. 
	- Description: Returns all Scores recorded by the provided player (unordered).
	Will raise a NotFoundException if the User does not exist.

- **get_user_games**
	- Path: 'games/user/{user_name}'
	- Method: GET
	- Parameters: user_name
	- Returns: GameForms
	- Description: Returns a list of all of the specified User's unfinished games.


## Models Included:
- **User**
	- Stores unique user_name and (optional) email address.

- **Game**
	- Stores unique game states. Associated with User model via KeyProperty.

- **Score**
	- Records completed games. Associated with Users model via KeyProperty.


## Forms Included:
- **GameForm**
	- Representation of a Game's state (urlsafe_key, best_of, game_over, message, user_name, player_wins, player_move, computer_wins, computer_move).
- **GameForms**
	- Multiple GameForm container.
- **NewGameForm**
	- Used to create a new game (user_name, best_of optional)
- **MakeMoveForm**
	- Inbound make move form ("Rock", "Paper", or "Scissors").
- **ScoreForm**
	- Representation of a completed game's Score (user_name, date, won flag, rounds played).
- **ScoreForms**
	- Multiple ScoreForm container.
- **StringMessage**
	- General purpose String container.
- **PerformanceForm**
	- Representation of a player's performance, or win record (user_name, win_rate percentage)
- **PerformanceForms**
	- Multiple PerformanceForm Container.
