import random
import datetime

from pymongo import MongoClient
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from bson import json_util


def users(request):
    client = MongoClient(
        'mongodb+srv://expressfood:expressfood@cluster0.c8ywndp.mongodb.net')
    db = client['expressfood']

    users_collection = db['users']

    # Vous pouvez maintenant récupérer les utilisateurs depuis la collection MongoDB
    users_list = list(users_collection.find({}))

    # Convertissez les données en JSON en utilisant json_util pour gérer les ObjectId
    data = {'users': json_util.dumps(users_list)}

    return JsonResponse(data, safe=False)

def daily_meals(request):

    # Vérifiez d'abord si les données sont déjà mises en cache
    cached_data = cache.get('random_meals_data')

    if cached_data:
        # Si les données sont en cache, renvoyez-les
        return JsonResponse({'random_meals': cached_data}, safe=False)
    
    client = MongoClient('mongodb+srv://expressfood:expressfood@cluster0.c8ywndp.mongodb.net')
    db = client['expressfood']

    meal_collection = db['meals']

    # Créez une pipeline d'agrégation pour regrouper les plats et les desserts
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

    # Exécutez la pipeline d'agrégation
    result = list(meal_collection.aggregate(pipeline))

    # Sélectionnez aléatoirement deux plats et deux desserts
    random_meals = []
    for group in result:
        meals = group['meals']
        if len(meals) >= 2:
            selected_meals = random.sample(meals, 2)
            random_meals.extend(selected_meals)

    # Convertissez les données en JSON en utilisant json_util
    data = {'random_meals': json_util.dumps(random_meals)}

    # Mettez en cache les données avec une expiration de 24 heures (86400 secondes)
    cache.set('random_meals_data', data['random_meals'], 86400)

    return JsonResponse(data, safe=False)

