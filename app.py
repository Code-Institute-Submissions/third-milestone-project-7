import os
from os import path
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, flash, render_template, redirect, request, url_for, Blueprint
from flask_paginate import Pagination, get_page_parameter
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, current_user, login_user
from bson.objectid import ObjectId
if path.exists("env.py"):
    import env

app = Flask(__name__)
mod = Blueprint("games", __name__)
login_manager = LoginManager(app)
login_manager.init_app(app)

app.config["MONGO_DBNAME"] = "third_milestone_project"
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

mongo = PyMongo(app)

# Games


@app.route("/")
@app.route("/game-list")
def game_list():
    search = False
    q = request.args.get("q")
    if q:
        search = True

    per_page = 5
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offset = (page - 1) * per_page

    games = mongo.db.game_list.find().limit(per_page).skip(offset)
    pagination = Pagination(per_page=per_page, page=page,
                            offset=offset, total=games.count(),
                            search=search, record_name="games",
                            css_framework="bootstrap4")

    return render_template("index.html",
                           games=games,
                           pagination=pagination
                           )


@app.route("/add-game")  # Display form page to add game
def add_game():
    return render_template("addgame.html")


# Add a new game
@app.route("/insert-game", methods=["POST"])
def insert_game():
    games = mongo.db.game_list
    games.insert_one(request.form.to_dict())
    return redirect(url_for("game_list"))


# Display more information on the selected game
# and displays relevant reviews
@app.route("/more-info/<game_list_id>")
def more_info(game_list_id):
    the_game = mongo.db.game_list.find_one({"_id": ObjectId(game_list_id)})
    all_categories = mongo.db.game_list.find()
    reviews = mongo.db.reviews.find({"game_id": ObjectId(game_list_id)})
    result = list(reviews)
    return render_template("moreinfo.html", game=the_game,
                           categories=all_categories, review=result)


# Display form page to edit game
@app.route("/edit-game-information/<game_list_id>")
def edit_game(game_list_id):
    the_game = mongo.db.game_list.find_one({"_id": ObjectId(game_list_id)})
    return render_template("editgame.html", game=the_game)


# Edit the chosen game
@app.route("/update-game/<game_list_id>", methods=["POST"])
def update_game(game_list_id):
    games = mongo.db.game_list
    games.update({"_id": ObjectId(game_list_id)},
                 {
        "game_name": request.form.get("game_name"),
        "game_genre": request.form.get("game_genre"),
        "game_pegi_rating": request.form.get("game_pegi_rating"),
        "game_image": request.form.get("game_image"),
        "fair_use": request.form.get("fair_use")
    })
    return redirect(url_for("game_list"))


# Delete a chosen game and it's reviews
@app.route("/delete-game/<game_list_id>")
def delete_game(game_list_id):
    mongo.db.game_list.delete_one({"_id": ObjectId(game_list_id)})
    mongo.db.reviews.delete_many({"game_id": ObjectId(game_list_id)})
    return redirect(url_for("game_list"))

# Reviews


# Display form to add review
@app.route("/add-review/<game_list_id>")
def add_review(game_list_id):
    the_game = mongo.db.game_list.find_one({"_id": ObjectId(game_list_id)})
    return render_template("addreview.html", game=the_game)


# Add the review
@app.route("/insert-review", methods=["POST"])
def insert_review():
    form_game_id = request.form.get("game_id")
    game_id = ObjectId(form_game_id)
    reviews = mongo.db.reviews
    reviews.insert_one({
        "game_id": game_id,
        "review": request.form.get("review")
    })
    return redirect(url_for("game_list"))


# Edit the current review
@app.route("/edit-review/<game_list_id>/<review_id>")
def edit_review(game_list_id, review_id):
    the_game = mongo.db.game_list.find_one({"_id": ObjectId(game_list_id)})
    the_review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    return render_template("editreview.html", game=the_game,
                           reviews=the_review)


# Update the review
@app.route("/update-review/<review_id>", methods=["POST"])
def update_review(review_id):
    form_game_id = request.form.get("game_id")
    game_id = ObjectId(form_game_id)
    reviews = mongo.db.reviews
    reviews.update({"_id": ObjectId(review_id)},
                   {
        "game_id": game_id,
        "review": request.form.get("review")
    })
    return redirect(url_for("game_list"))


# Delete a chosen review
@app.route("/delete-review/<review_id>")
def delete_review(review_id):
    mongo.db.reviews.delete_one({"_id": ObjectId(review_id)})
    return redirect(url_for("game_list"))


"""
Add in the CRUD architecture:

* Create: Reviews - Added (Works, have to return to the main page)
* Read: Done
* Update: Reviews - Added (Works, have to return to the main page)
* Delete: Reviews - Added (Works, have to return to the main page)

TODO:
    * Create a function to delete a single key:value pair from a
    * dataset by selecting the value you wish to remove
"""

"""
TODO:
    * Create login system, and use database to store emails,
    * usernames and passwords
    * Allow only the deletion of reviews the logged in user has posted
"""
# Login system


"""class User(UserMixin, mongo.db.user_data):
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_data_id):
    user_id = mongo.db.user_data({"_id": ObjectId(user_data_id)})
    return User.query.get(user_id)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)"""

# Contact Page


@app.route("/contactus")  # Contact information page poss using an email API
def contact():
    return redirect("contact.html")


if __name__ == "__main__":
    app.run(host=os.getenv("IP"),
            port=int(os.getenv("PORT")), debug=True)
