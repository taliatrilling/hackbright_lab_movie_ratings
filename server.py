"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request,
    flash, session, make_response)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


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
                return redirect("/") 
        else: 
            flash("Your password was invalid, please try again")
            return render_template("sign_in.html")

@app.route("/logout")
def logout_success():
    """Logs out user by deleting the session associated with their account, redirects to homepage"""

    del session["username"]
    return redirect("/")



if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)


    app.run(port=5000)
    
    # app.run(port=5003)
