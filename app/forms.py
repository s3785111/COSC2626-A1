from cloud import tables
from importlib import import_module
from flask import current_app
from wtforms import Form, StringField, ValidationError
from wtforms.validators import Email, InputRequired


class ExistsInTable(object):
    def __init__(self, attribute, table, desired=True, message=None):
        self.attribute = attribute
        self.table = table
        self.desired = desired
        self.message = message

    def __call__(self, form, field):
        message = (
            self.message
            or f'{self.attribute.capitalize()} {field.data} {"must" if self.desired else "must not"} exist'
        )
        exists = getattr(import_module("cloud.tables"), self.table.capitalize())(
            current_app.extensions["db"]
        ).query_key(self.attribute, field.data)["Count"]
        if exists and not self.desired or not exists and self.desired:
            raise ValidationError(message)


class LoginForm(Form):
    def validate_password(self, field):
        login_table = tables.Login(current_app.extensions["db"])
        res = login_table.query_key("email", self.data["email"])

        if not (res["Count"] and res["Items"][0].get("password") == field.data):
            raise ValidationError("Incorrect email or password")

    email = StringField(
        validators=[InputRequired(), Email(), ExistsInTable("email", "login")]
    )
    password = StringField(validators=[InputRequired(), validate_password])
