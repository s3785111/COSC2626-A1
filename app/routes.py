import json
import logging
from auth import User
from forms import LoginForm, RegisterForm, QueryForm
from cloud import tables
from importlib import import_module
from flask import current_app, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

logger = logging.getLogger(__name__)


@current_app.route("/", methods=["GET", "POST"])
@login_required
def root():
    form = QueryForm(request.form)

    if request.method == "GET":
        return render_template("home.html", form=form)
    else:
        music_table = tables.Music(current_app.extensions["db"])

        # Filter by attributes and both hash and range keys if available
        if form.data["artist"] and form.data["title"]:
            keys = {
                "artist": form.data["artist"],
                "title": form.data["title"]
            }
            attributes = {"year": form.data["year"]}
        # Filter atttributes and only hash key
        elif form.data["artist"]:
            keys = {
                "artist": form.data["artist"]
            }
            attributes = {
                "year": form.data["year"],
                "title": form.data["title"]
            }
        # Filter by attributes only
        else:
            keys = None
            attributes = {
                "year": form.data["year"],
                "title": form.data["title"]
            }
        results = music_table.query(keys, attributes)["Items"]
        return render_template("home.html", form=form, results=results)


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
def database(table):
    table_ = getattr(import_module("cloud.tables"), table.capitalize())(
        current_app.extensions["db"]
    )
    items_formatted = [
        json.dumps(item, indent=2) for item in table_.query()["Items"]
    ]
    return render_template(
        "database.html", table_name=table, database_items=items_formatted
    )
