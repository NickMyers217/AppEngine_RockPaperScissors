# -*- coding: utf-8 -*-`
"""api.py - This file contains all of th API code for the Rock Paper Scissors game."""

import random
import logging
import endpoints

from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from utils import get_by_urlsafe
from models import (
        User,
        Game,
        Score,
        StringMessage,
        NewGameForm,
        GameForm,
        MakeMoveForm,
        ScoreForms,
        GameForms,
        PerformanceForms,
        StringMessages,
)

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(
        user_name=messages.StringField(1),
        email=messages.StringField(2),)

@endpoints.api(name='rock_paper_scissors', version='v1')
class RockPaperScissorsAPI(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException('A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))


    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('A User with that name does not exist!')
        try:
            game = Game.new_game(user.key, request.best_of)
        except ValueError:
            raise endpoints.BadRequestException('best_of must be an odd number!')

        return game.to_form('Good luck playing rock paper scissors!')


    @endpoints.method(request_message=GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=GAME_REQUEST,
                      response_message=StringMessages,
                      path='history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return a game's move history"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return StringMessages(items=game.move_history)
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Cancel a game"""
        # Get the game
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')

        # Make sure the game is not complete
        if(game.game_over):
            return StringMessage(message='Cannot cancel a completed game!')

        # Delete the game
        game.key.delete()
        return StringMessage(message='Game deleted!')


    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        # Get the game and make sure it is still in progress
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')

        if game.game_over:
            return game.to_form('Game already over!')

        # Check the request to make sure the move is valid
        MOVES = ['rock', 'paper', 'scissors']
        if request.move.lower() not in MOVES:
            return game.to_form('Invalid move!')

        # Assign the player and computer moves
        game.player_move = request.move.lower()
        game.computer_move = MOVES[random.choice(range(3))]

        # Add the move to the game's history
        history = 'Player Move: {}, Computer Move: {}' \
            .format(game.player_move, game.computer_move)

        # Check to see if the round is a tie
        if game.player_move == game.computer_move:
            game.move_history.append('{}, Result: tie'.format(history))
            game.put()
            return game.to_form('This round was a tie!')

        # Check all the possible scenarios and adjust the wins
        msg = ''
        if game.player_move == 'rock':
            if game.computer_move == 'paper':
                game.computer_wins += 1
                msg = 'Paper beats rock!  Computer wins this round!'
            if game.computer_move == 'scissors':
                game.player_wins += 1
                msg = 'Rock beats scissors!  Player wins this round!'
        if game.player_move == 'scissors':
            if game.computer_move == 'rock':
                game.computer_wins += 1
                msg = 'rock beats scissors!  Computer wins this round!'
            if game.computer_move == 'paper':
                game.player_wins += 1
                msg = 'Scissors beats rock! Player wins this round'
        if game.player_move == 'paper':
            if game.computer_move == 'scissors':
                game.computer_wins += 1
                msg = 'Scissors beats paper! Computer wins this round!'
            if game.computer_move == 'rock':
                game.player_wins += 1
                msg = 'Paper beats rock! Player wins this round!'

        # See if anyone has won, if so end the game
        if game.player_wins > game.best_of / 2:
            game.end_game(True)
            game.move_history.append('{}, Result: player win'.format(history))
            game.put()
            return game.to_form('You win!')
        elif game.computer_wins > game.best_of / 2:
            game.end_game(True)
            game.move_history.append('{}, Result: computer win'.format(history))
            game.put()
            return game.to_form('You lost!')
        else:
            # The game is still in progress
            game.move_history.append('{}, Result: {}'.format(history, msg))
            game.put()
            return game.to_form(msg)


    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])


    @endpoints.method(response_message=PerformanceForms,
                      path='rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return all of the users ranked by there win / loss ratio"""
        return PerformanceForms(items=sorted([user.to_perf_form()
            for user in User.query()],
            key=lambda p: p.win_rate,
            reverse=True))


    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])


    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of an individual User's unfinished games"""
        # Get the user and make sure they exist
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('A User with that name does not exist!')

        # Query for this users active games
        games = Game \
            .query(Game.user == user.key) \
            .filter(Game.game_over == False)

        # Convert the games to a GameForms
        return GameForms(items=[game.to_form('Time to make a move!')
            for game in games])


api = endpoints.api_server([RockPaperScissorsAPI])
