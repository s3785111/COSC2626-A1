import os
import logging
import configparser
import boto3
from flask import Flask

PROJDIR = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s — %(levelname)s %(name)s — %(funcName)s:%(lineno)d — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=f"{PROJDIR}/app.log",
    filemode="a",
)
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("botocore").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


def init_app():
    app = Flask(__name__)

    try:
        config = configparser.ConfigParser()
        config.read("config.ini")
        app.config["SECRET_KEY"] = config["flask"]["SECRET_KEY"]
        app.config["DB_ENDPOINT"] = config["dynamodb"]["DB_ENDPOINT"]
    except FileNotFoundError:
        logger.warning("Config no found, defaults will be loaded")

    logger.debug(app.config)

    app.extensions["db"] = boto3.resource(
        "dynamodb", endpoint_url=app.config.get("DB_ENDPOINT", "http://localhost:8000")
    )

    with app.app_context():
        import auth
        import routes
        from cloud import tables
        from auth import login_manager

        login_manager.init_app(app)

    return app
