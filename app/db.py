from dotenv import load_dotenv, find_dotenv
import os
from pymongo import MongoClient
load_dotenv(find_dotenv())

password = os.environ.get("MONGODB_PWD")
print(f"Password cargada: {password}")

connection_string = f"mongodb+srv://edjoel05:{password}@server1.jns05ba.mongodb.net/?retryWrites=true&w=majority&appName=SERVER1"
client = MongoClient(connection_string)
dbs = client.list_database_names()
chatbot_db = client.chatbot
collection = chatbot_db.list_collection_names()

#How to insert data into one of the collections in the chatbot database

"""
def insterts_chatbot_doc():
    collection = chatbot_db.mate
    test_instert = {
        "name": "Mate",
        "description": "A chatbot that helps you with your daily tasks.",
    }
    inserted_id = collection.insert_one(test_instert).inserted_id
    print(inserted_id)
insterts_chatbot_doc()
"""

#How to do an insertMany operation in a collection

"""
test = client.test
test_collection = test.test_collection

def insertMany_test():
    test_names = ["Alice", "Bob", "Charlie"]
    test_ages = [25, 30, 35]

    docs = []

    for name, age in zip(test_names, test_ages):
        doc = {"fist_name": name, "age": age}
        docs.append(doc)
    test_collection.insert_many(docs)
insertMany_test()
"""

# How to do a find operation in a collection

def find_chatbot_doc():
    chatbot_db = collection.find()