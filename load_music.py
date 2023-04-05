import os
import sys
import json
from flask import current_app
from app.cloud import tables

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) + "/app"
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)
from app.app import init_app

with init_app().app_context():
    with open("static/a1.json", "r") as f:
        music_table = tables.Music(current_app.extensions["db"])
        music_table.load_batch(f.read())
