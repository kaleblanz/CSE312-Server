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

video_collection = db['videos']

"""
class Deez():
    def __init__(self):
        self.roof = ""



object_1 = Deez()
object_2 = Deez()
object_3 = Deez()
object_4 = Deez()
print("obj1:",object_1)
print("obj2:",object_2)
print("obj3:",object_3)
print("obj4:",object_4)

user_list = [{"username" : 'bob', "tcp" : object_1}, {"username" : 'steve', "tcp" : object_2}, {"username" : 'ricky', "tcp" : object_3},{"username" : 'jack', "tcp" : object_4}]
print(user_list)
user_list.remove({"username" : 'jack', "tcp" : object_4})
print(user_list)
"""