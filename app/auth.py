import logging
from cloud import tables
from flask import current_app
from flask_login import LoginManager, UserMixin


login_manager = LoginManager()
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = password

    def get_id(self):
        try:
            return str(self.email)
        except AttributeError:
            raise NotImplementedError("No `id` attribute - override `get_id`") from None


@login_manager.user_loader
def load_user(user_id):
    login_table = tables.Login(current_app.extensions["db"])
    res = login_table.query_key("email", user_id)
    return (
        User(
            email=res["Items"][0].get("email"),
            username=res["Items"][0].get("username"),
            password=res["Items"][0].get("password"),
        )
        if res["Count"]
        else None
    )
