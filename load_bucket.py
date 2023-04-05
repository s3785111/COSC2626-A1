import os
import sys
import json
from app.cloud import s3

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/app'
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)
from app import init_app

with init_app().app_context():
    with open("static/a1.json", "r") as f:
        songs = json.loads(f.read())["songs"]
        for song in songs:
            s3.upload_from_url(song["img_url"])
