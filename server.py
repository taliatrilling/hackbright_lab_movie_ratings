"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request,
    flash, session, make_response)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db

from datetime import datetime

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route("/users")
def user_list():
    """Show list of users"""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route("/sign-in")
def sign_in():
    """Allows user to sign in"""

    return render_template("sign_in.html")


@app.route("/sign-in-success", methods=["POST", "GET"])
def sign_in_success():
    """Checks if username in system"""

    error = None

    username = request.form.get("username")
    password = request.form.get("password")


    if not User.query.filter(User.email == username).first():
        user = User(email=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("You are successfully logged in, %s" % username)
        session["username"] = username
        return redirect("/") 
    else:
        if User.query.filter(User.email == username, User.password == password).first():
            if request.method == "POST":
                flash("You are successfully logged in, %s" % username)
                session["username"] = username
                my_user_id = db.session.query(User.user_id).filter(User.email == username, User.password == password).first()
                return redirect("/user?user_id=" + str(my_user_id[0])) 
        else: 
            flash("Your password was invalid, please try again")
            return render_template("sign_in.html")


@app.route("/logout")
def logout_success():
    """Logs out user by deleting the session associated with their account, redirects to homepage"""

    del session["username"]
    flash("You have been successfully logged out")
    return redirect("/")


@app.route("/user")
def show_user():
    """Shows the information associated with a specific user, defaults to show talia"""

    username = request.args.get("user_id", 945)

    if User.query.filter(User.user_id == username).first():
        age = db.session.query(User.age).filter(User.user_id == username).first()
        zipcode = db.session.query(User.zipcode).filter(User.user_id == username).first()
        email = db.session.query(User.email).filter(User.user_id == username).first()
        user_ratings = db.session.query(Rating.movie_id, Rating.score).filter(Rating.user_id == username).all()
        movie_titles = []
        for item in user_ratings:
            my_movie_id = item[0]
            title = db.session.query(Movie.title).filter(Movie.movie_id == my_movie_id).first()
            movie_titles.append(title)
        return render_template("user.html", username=username, age=age, zipcode=zipcode,
            email=email, user_ratings=user_ratings, movie_titles=movie_titles)
    else:
        flash("That user does not currently exist in the database.")
        return redirect ("/users")


@app.route("/movies")
def show_movies():
    """Shows all the movies in the database along with links to the individual pages for these movies"""

    movies = Movie.query.order_by(Movie.title).all()

    return render_template("movies.html", movies=movies)


@app.route("/movie")
def show_individual_movie():
    """Shows the details associated with a particular movie, defaults to showing 101 Dalmations"""

    my_movie_id = request.args.get("movie_id", 225)
    movie = Movie.query.get(my_movie_id)

    if Movie.query.filter(Movie.movie_id == my_movie_id).first():
        if "username" in session.keys():
            user_email = session["username"]
            user_id = db.session.query(User.user_id).filter(User.email == user_email).first()
            user_rating = Rating.query.filter(Rating.movie_id == my_movie_id, Rating.user_id == user_id).first()
        else:
            user_rating = None

        rating_scores = [r.score for r in movie.ratings]
        avg_rating = float(sum(rating_scores)) / len(rating_scores)

        prediction = None

        if (not user_rating) and "username" in session.keys():
            user = User.query.get(user_id)
            if user:
                prediction = user.predict_rating(my_movie_id)


        title = db.session.query(Movie.title).filter(Movie.movie_id == my_movie_id).first()
        release_date = db.session.query(Movie.released_at).filter(Movie.movie_id == my_movie_id).first()
        release_date = datetime.strftime(release_date[0], "%B %d, %Y")
        imdb_url = db.session.query(Movie.imdb_url).filter(Movie.movie_id == my_movie_id).first()
        user_ratings = db.session.query(Rating.user_id, Rating.score).filter(Rating.movie_id == my_movie_id).all()
        all_ratings = []
        for item in user_ratings:
            all_ratings.append(item)

        if prediction:
            effective_rating = prediction
        elif user_rating:
            effective_rating = user_rating.score
        else:
            effective_rating = None

        the_eye = (User.query.filter(User.email == "the-eye@of-judgment.com").one())
        eye_rating = Rating.query.filter(Rating.user_id == the_eye.user_id, Rating.movie_id == movie.movie_id).first()

        if eye_rating is None:
            eye_rating = the_eye.predict_rating(my_movie_id)
        else:
            eye_rating = eye_rating.score

        if eye_rating and effective_rating:
            difference = abs(eye_rating - effective_rating)
        else:
            difference = None

        BERATEMENT_MESSAGES= ["I suppose you don't have such bad taste after all.", 
        "I regret every decision that I've ever made that has brought me to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly failed you.",
        "That movie is great. For a clown to watch. Idiot.", 
        "Words cannot express the awfulness of your taste."]

        if difference is not None:
            beratement = BERATEMENT_MESSAGES[int(difference)]
        else:
            beratement = None

        return render_template("movie.html", title=title, release_date=release_date, imdb_url=imdb_url,
            all_ratings=all_ratings, my_movie_id=my_movie_id, user_rating=user_rating, average=avg_rating,
            prediction=prediction, beratement=beratement)
    else:
        flash("That movie does not currently exist in the database.")
        return redirect ("/movies")


@app.route("/process-score", methods=["POST"])
def set_score():
    """Checks if the user has already set a score for the movie in question, if so, updates it, otherwise 
    adds a new score for that user and that movie"""

    new_score = request.form.get("score")
    my_movie_id = int(request.form.get("movieid"))
    username = session["username"]
    my_user_id = db.session.query(User.user_id).filter(User.email==username).first()

    if db.session.query(Rating.score).filter(Rating.movie_id == my_movie_id, 
        Rating.user_id == my_user_id).first():
        rating = db.session.query(Rating).filter(Rating.movie_id == my_movie_id, 
        Rating.user_id == my_user_id).first()
        rating.score = new_score
        db.session.commit()
        flash("Your rating was successfully updated.")
        return redirect ("/movie?movie_id=" + str(my_movie_id))
    else:
        rating = Rating(user_id=my_user_id, movie_id=my_movie_id, score=new_score)
        db.session.add(rating)
        db.session.commit()
        flash("Your new rating was successfully added.")
        return redirect ("/movie?movie_id=" + str(my_movie_id))


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)


    app.run(port=5000)
    
    # app.run(port=5003)
