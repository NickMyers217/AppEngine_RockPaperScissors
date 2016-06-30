"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name  = ndb.StringProperty(required=True)
    email = ndb.StringProperty()

    def get_win_rate(self):
        """Return the user's win percentage as a float"""
        # Get all of the games this user has finished
        scores = Score.query(Score.user == self.key)

        # Tally up their wins and losses
        won  = 0.0
        lost = 0.0
        for s in scores:
            if s.won:
                won += 1.0
            else:
                lost += 1.0

        # Calculate win percentage
        return won / (won + lost) * 100.0


    def to_perf_form(self):
        """Convert the user to a performance form"""
        form = PerformanceForm()
        form.user_name = self.name
        form.win_rate  = self.get_win_rate()
        return form


class Game(ndb.Model):
    """Game object"""
    best_of       = ndb.IntegerProperty(required=True)
    game_over     = ndb.BooleanProperty(required=True)
    user          = ndb.KeyProperty(required=True, kind='User')
    player_wins   = ndb.IntegerProperty(required=False, default=0)
    player_move   = ndb.StringProperty(required=False, default="Rock")
    computer_wins = ndb.IntegerProperty(required=False, default=0)
    computer_move = ndb.StringProperty(required=False, default="Rock")

    @classmethod
    def new_game(self, user, best_of):
        """Creates and returns a new game"""
        if best_of % 2 == 0:
            raise ValueError('best_of must be an odd number!')
        game = Game(user=user,
                    best_of=best_of,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key   = self.key.urlsafe()
        form.user_name     = self.user.get().name
        form.best_of       = self.best_of
        form.game_over     = self.game_over
        form.message       = message
        form.player_wins   = self.player_wins
        form.player_move   = self.player_move
        form.computer_wins = self.computer_wins
        form.computer_move = self.computer_move
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()

        won = False
        if self.player_wins > self.computer_wins:
            won = True

        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      rounds=self.player_wins + self.computer_wins)
        score.put()


class Score(ndb.Model):
    """Score object"""
    user    = ndb.KeyProperty(required=True, kind='User')
    date    = ndb.DateProperty(required=True)
    won     = ndb.BooleanProperty(required=True)
    rounds  = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), rounds=self.rounds)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key   = messages.StringField(1, required=True)
    best_of       = messages.IntegerField(2, required=True)
    game_over     = messages.BooleanField(3, required=True)
    message       = messages.StringField(4, required=True)
    user_name     = messages.StringField(5, required=True)
    player_wins   = messages.IntegerField(6, required=True)
    player_move   = messages.StringField(7, required=True)
    computer_wins = messages.IntegerField(8, required=True)
    computer_move = messages.StringField(9, required=True)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    best_of   = messages.IntegerField(2, default=3)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    move = messages.StringField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date      = messages.StringField(2, required=True)
    won       = messages.BooleanField(3, required=True)
    rounds    = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class PerformanceForm(messages.Message):
    user_name = messages.StringField(1, required=True)
    win_rate  = messages.FloatField(2, required=True)


class PerformanceForms(messages.Message):
    items = messages.MessageField(PerformanceForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
