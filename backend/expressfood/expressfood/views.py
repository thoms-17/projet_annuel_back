import random
import os

from pymongo import MongoClient
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from bson import json_util
from dotenv import load_dotenv, find_dotenv

host = os.getenv('MONGODB_HOST')
name = os.getenv('MONGODB_NAME')

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(host)
        self.db = self.client[name]

    def get_users_collection(self):
        return self.db['users']

    def get_meal_collection(self):
        return self.db['meals']

    def get_order_collection(self):
        return self.db['order']

# Initialisez une seule instance de DatabaseManager
db_manager = DatabaseManager()

def users(request):
    users_collection = db_manager.get_users_collection()
    users_list = list(users_collection.find({}))
    data = {'users': json_util.dumps(users_list)}
    return JsonResponse(data, safe=False)

def daily_meals(request):
    cached_data = cache.get('random_meals_data')
    if cached_data:
        return JsonResponse({'random_meals': cached_data}, safe=False)

    meal_collection = db_manager.get_meal_collection()

    pipeline = [
        {
            '$match': {
                'type': {'$in': ['plat', 'dessert']}
            }
        },
        {
            '$group': {
                '_id': '$type',
                'meals': {'$push': '$$ROOT'}
            }
        }
    ]

    result = list(meal_collection.aggregate(pipeline))

    # Sélectionnez aléatoirement deux plats et deux desserts
    random_meals = []
    for group in result:
        meals = group['meals']
        if len(meals) >= 2:
            selected_meals = random.sample(meals, 2)
            random_meals.extend(selected_meals)

    data = {'random_meals': json_util.dumps(random_meals)}
    cache.set('random_meals_data', data['random_meals'], 86400)
    return JsonResponse(data, safe=False)

def order(request):
    order_collection = db_manager.get_order_collection()
    order_list = list(order_collection.find({}))
    data = {'order': json_util.dumps(order_list)}
    return JsonResponse(data, safe=False)

def register(request):
    # On récupère les données envoyées par le client
    data = request.POST

    # On vérifie que l'utilisateur n'existe pas déjà
    users_collection = db_manager.get_users_collection()

    user = users_collection.find_one({'email': data['email']})

    if user:
        return HttpResponse('User already exists', status=400)

    # On crée l'utilisateur
    user = {
        'nom': data['nom'],
        'prenom': data['prenom'],
        'email': data['email'],
        'password': data['password'],
        'adresse': data['adresse'],
    }

    # On l'insère dans la base de données
    users_collection.insert_one(user)

    return HttpResponse('User created', status=201)

def login(request):
    # On récupère les données envoyées par le client
    data = request.POST

    # On vérifie que l'utilisateur existe
    users_collection = db_manager.get_users_collection()

    user = users_collection.find_one({'email': data['email']})

    if not user:
        return HttpResponse('User not found', status=404)

    # On vérifie que le mot de passe est correct
    if user['password'] != data['password']:
        return HttpResponse('Wrong password', status=400)

    return HttpResponse('User logged in', status=200)
