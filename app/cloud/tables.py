import logging
import json
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError


log = logging.getLogger(__name__)


class BaseTable:
    """Base class for objects wrapping DynamoDB Table"""

    def __init__(self, db, **properties):
        self.db = db
        self.properties = properties

        # Initialise table to existing resource if possible, otherwise create new table
        self._table = self.__get_table() if self.__exists() else self.__create_table()

    def __exists(self):
        return any(
            table.name == self.properties["TableName"]
            for table in list(self.db.tables.all())
        )

    def __get_table(self):
        try:
            table = self.db.Table(self.properties["TableName"])
            table.load()
            log.debug(f"Loaded table at {table}")
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                log.debug(f'No table found with name {self.properties["TableName"]}')
                table = None
            else:
                log.error(err.response)
                raise

        return table

    def __create_table(self):
        try:
            log.debug(f'Creating table {self.properties["TableName"]}')
            log.debug(f"Table has properties {self.properties}")
            table = self.db.create_table(**self.properties)
            table.wait_until_exists()
        except Exception as err:
            log.error(err)
            raise

        return table

    def query_all(self):
        return self._table.scan()

    def query_key(self, key_name, query_value):
        return self._table.query(KeyConditionExpression=Key(key_name).eq(query_value))

    def load_obj(self, obj):
        try:
            self._table.put_item(Item=obj)
        except Exception as err:
            log.error(err)
            raise

    def load_batch(self, batch):
        try:
            with self._table.batch_writer() as write:
                for item in batch:
                    write.put_item(Item=item)
        except ClientError as err:
            log.error(err)
            raise


class Music(BaseTable):
    def __init__(self, db):
        super().__init__(
            db,
            TableName="music",
            KeySchema=[
                {"AttributeName": "artist", "KeyType": "HASH"},
                {"AttributeName": "title", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "artist", "AttributeType": "S"},
                {"AttributeName": "title", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
        )

    def load_batch(self, batch_json):
        batch = json.loads(batch_json)["songs"]
        super().load_batch(batch)


class Login(BaseTable):
    def __init__(self, db):
        super().__init__(
            db,
            TableName="login",
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
        )

    def load_batch(self, batch_json):
        batch = json.loads(batch_json)
        super().load_batch(batch)
