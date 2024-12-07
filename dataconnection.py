import json
from pymongo import MongoClient
from apscheduler.schedulers.blocking import BlockingScheduler
import time

client = MongoClient("mongodb+srv://kundan:kundankumar@cluster0.psuhr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["kundan"]
users_collection = db["users"]

def read_card_data(filename="C:/Users/sarth/OneDrive/Desktop/sarangi.bot/sarangi-discord-bot/data.json"):
    with open(filename, "r") as file:
        data = json.load(file)
    return data

def update_mongodb_with_card_data(data):
    for user_group in ['userA', 'userB']:
        for user in data.get(user_group, []):
            user_id = user['user_id']
            user_points = user.get('points', 0) 

            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id, "points": user_points, "name": user.get('name', '')}},  
                upsert=True
            )
            for card in user.get('cards', []):
                card_user_id = card['user_id']
                db['cards'].update_one(
                    {"user_id": card_user_id, "name": card['name']},
                    {"$set": card},
                    
                    upsert=True
                )
    for card in data.get('available_cards', []):
        db['available_cards'].update_one(
            {"user_id": card['user_id'], "name": card['name']},
            {"$set": card},
            upsert=True
        )

def update_data_in_mongo():
    card_data = read_card_data("C:/Users/sarth/OneDrive/Desktop/sarangi.bot/sarangi-discord-bot/data.json")
    update_mongodb_with_card_data(card_data)
    print("MongoDB database has been updated with the latest card data!")

scheduler = BlockingScheduler()

scheduler.add_job(update_data_in_mongo, 'interval', seconds=1)
print("Scheduler started. MongoDB will be updated every second.")
scheduler.start
