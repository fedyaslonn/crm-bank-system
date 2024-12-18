import pymongo
import datetime

# MongoDB settings
MONGO_DATABASE_NAME = 'Notifications'
mongo_url = "mongodb+srv://wisp47344:Agcacjqf5144@cluster0.8093p.mongodb.net/"


# # Connect to MongoDB
# try:
#     client = pymongo.MongoClient(mongo_url)
#     db = client[MONGO_DATABASE_NAME]
#     print("Connection to MongoDB successful!")
# except Exception as e:
#     print(f"Connection to MongoDB failed: {e}")
#
# # Создание коллекции и вставка документа
# try:
#     collection = db['Notification']
#     notification = {
#         'title': 'Test Notification',
#         'content': 'This is a test notification',
#         'created_at': datetime.datetime.utcnow()
#     }
#     result = collection.insert_one(notification)
#     print(f"Document inserted with ID: {result.inserted_id}")
# except Exception as e:
#     print(f"Error creating collection 'Notification': {e}")