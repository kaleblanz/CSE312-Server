import json
import sys
import os

from pymongo import MongoClient

docker_db = os.environ.get('DOCKER_DB', "false")

if docker_db == "true":
    print("using docker compose db")
    mongo_client = MongoClient("mongo")
else:
    print("using local db")
    mongo_client = MongoClient("localhost")

db = mongo_client["cse312"]

chat_collection = db["chat"]

user_collection = db["users"]

test_collection = db["test_collection"]


"""
test_collection.insert_one({"name":"kaleb","age":"123213"})
print(test_collection.find_one({}))
result = test_collection.update_one({"name":"kaleb"},{"$set":{"age":"213321"}})
#UpdateResult({'n': 1, 'nModified': 1, 'ok': 1.0, 'updatedExisting': True}, acknowledged=True)
print(test_collection.find_one({}))
print(result)
"""