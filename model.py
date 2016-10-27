"""Models and database functions for Ratings project."""

from flask_sqlalchemy import SQLAlchemy

import correlation

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.String(64), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    zipcode = db.Column(db.String(15), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed"""

        return "<User user_id=%s email=%s>" % (self.user_id, self.email)

    def similarity(self, other):
        """Return Pearson rating for user compared to other user"""

        user_ratings = {}
        paired_ratings = []

        for user_rating in self.ratings:
            user_ratings[user_rating.movie_id] = user_rating

        for other_rating in other.ratings:
            r = user_ratings.get(other_rating.movie_id) # my rating for other's movie
            if r:
                paired_ratings.append( (r.score, other_rating.score) )

        if paired_ratings:
            return correlation.pearson(paired_ratings)

        else:
            return 0.0

    def predict_rating(self, movie):
        """Predict a user's rating of a movie"""

        other_ratings = movie.ratings

        similarities = [(self.similarity(r.user), r) for r in other_ratings]

        similarities.sort(reverse=True)

        similarities = [(sim, r) for sim, r in similarities if sim > 0]

        if not similarities:
            return None

        numerator = sum([r.score * sim for sim, r in similarities])
        denominator = sum([sim for sim, r in similarities])

        return numerator/denominator

# Put your Movie and Rating model classes here.

class Movie(db.Model):
    """Movie on ratings website"""

    __tablename__ = "movies"

    movie_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    released_at = db.Column(db.DateTime, nullable=True)
    imdb_url = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        """Provide helpful representation when printed"""

        return "<Movie movie_id=%s title=%s released_at=%s imdb_url%s>" % (self.movie_id,
            self.title, self.released_at, self.imdb_url)

class Rating(db.Model):
    """Rating for a movie by a specific user on ratings website"""

    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.movie_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    user = db.relationship("User", backref=db.backref("ratings", order_by=rating_id))

    movie = db.relationship("Movie", backref=db.backref("ratings", order_by=rating_id))


    def __repr__(self):
        """Provide helpful representation when printed"""

        s = "<Rating rating_id=%s movie_id=%s user_id=%s score=%s>"
        return s % (self.rating_id, self.movie_id, self.user_id, self.score)


##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ratings'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
