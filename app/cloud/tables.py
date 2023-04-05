import logging
import json
from functools import reduce
from boto3.dynamodb.conditions import Attr, Key, And, Or
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

    def query(self, keys=None, attributes=None, condition=And):
        """ 
        General query method. Can query by keys, keys and attributes, or attributes.
        If no keys or attributes are provided, table scan is performed.
        """
        key_reducable = (
            [Key(k).eq(v) for k, v in keys.items() if v] if keys else None
        )  # Filter expression for keys only on non-empty keys
        filter_reducable = (
            [Attr(k).eq(v) for k, v in attributes.items() if v] if attributes else None
        )  # Filter expression for attributes only on non-empty attributes

        # Query on keys and attributes
        if key_reducable and filter_reducable:
            results = self._table.query(
                KeyConditionExpression=reduce(condition, key_reducable),
                FilterExpression=reduce(condition, filter_reducable) if filter_reducable else None,
            )
        # Query on attributes only
        elif not key_reducable and filter_reducable:
            results = self._table.scan(
                FilterExpression=reduce(condition, filter_reducable)
            )
        # Query all
        else:
            return self._table.scan()

        return results

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


class Subscriptions(BaseTable):
    def __init__(self, db):
        super().__init__(
            db,
            TableName="subscriptions",
            KeySchema=[
                {"AttributeName": "user", "KeyType": "HASH"},
                {"AttributeName": "subId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user", "AttributeType": "S"},
                {"AttributeName": "subId", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
        )


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
