from flask import current_app, url_for
from pathlib import Path
import requests
import json
import boto3


s3 = boto3.resource("s3")

bucket_name = current_app.config.get("BUCKET_NAME", "")
bucket = s3.Bucket(bucket_name)


def upload_from_url(url):
    filename = Path(url).name
    r = requests.get(url, stream=True)
    key = filename
    bucket.upload_fileobj(r.raw, key)
