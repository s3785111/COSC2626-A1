import json
import logging
from auth import User
from cloud import tables
from forms import LoginForm, RegisterForm, QueryForm, SubscriptionForm
from importlib import import_module
from itertools import zip_longest
from flask import current_app, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user

logger = logging.getLogger(__name__)


@current_app.route("/", methods=["GET", "POST"])
@login_required
def root():
    query_form = QueryForm(request.form)
    sub_form = SubscriptionForm(request.form)
    results = None

    music_table = tables.Music(current_app.extensions["db"])

    # Query request
    if request.method == "GET" or request.form["action"] == "query":
        keys = None
        attributes = {
            "artist": query_form.data["artist"],
            "year": query_form.data["year"],
            "title": query_form.data["title"]
        }
        results = music_table.query(keys, attributes)["Items"]
    # Subscribe request
    elif request.form["action"] == "subscribe":
        subscription = {
            "user": sub_form.data["user"],
            "song_id": sub_form.data["song_id"],
        }
        tables.Subscriptions(current_app.extensions["db"]).load_obj(subscription)
    # Unubscribe request
    elif request.form["action"] == "unsubscribe":
        subscription = {
            "user": sub_form.data["user"],
            "song_id": sub_form.data["song_id"],
        }
        tables.Subscriptions(current_app.extensions["db"]).delete_obj(subscription)

    subs_table = tables.Subscriptions(current_app.extensions["db"])
    subs = subs_table.query(keys={"user": current_user.email})["Items"]

    # Add song details to subs if necessary
    if subs:
        # Get list of songs matching to sub list
        subs_songs = music_table.query(
            attributes={"song_id": [sub["song_id"] for sub in subs]},
            attr_condition="is_in",
        )["Items"]
        # From https://stackoverflow.com/questions/5501810/join-two-lists-of-dictionaries-on-a-single-key
        # Get list of dicts combining song and sub info
        subs = [{**u, **v} for u, v in zip_longest(subs, subs_songs, fillvalue={})]

    return render_template(
        "home.html",
        query_form=query_form,
        sub_form=sub_form,
        results=results,
        subs=subs,
        bucket=current_app.config.get("BUCKET_NAME", ""),
    )


@current_app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "GET" and current_user.is_authenticated:
        return redirect(url_for("root"))
    elif request.method == "POST" and form.validate():
        login_table = tables.Login(current_app.extensions["db"])
        res = login_table.query(keys={"email": form.data["email"]})
        user = User(
            res["Items"][0].get("email"),
            res["Items"][0].get("username"),
            res["Items"][0].get("password"),
        )
        login_user(user, remember=True)
        return redirect(url_for("root"))
    else:
        return render_template("login.html", form=form)


@current_app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("root"))


@current_app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        user = User(
            form.data["email"],
            form.data["username"],
            form.data["password"],
        )
        login_user(user, remember=True)
        tables.Login(current_app.extensions["db"]).load_obj(vars(user))
        return redirect(url_for("root"))
    else:
        return render_template("register.html", form=form)


@current_app.route("/debug/<table>")
def debug(table):
    table_ = getattr(import_module("cloud.tables"), table.capitalize())(
        current_app.extensions["db"]
    )
    items_formatted = [json.dumps(item, indent=2) for item in table_.query()["Items"]]
    return render_template(
        "database.html", table_name=table, database_items=items_formatted
    )
