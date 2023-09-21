import random
import os
import json

from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from bson import json_util
from dotenv import load_dotenv, find_dotenv

load_dotenv()

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

@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            # Extrait les données JSON du corps de la requête
            data = json.loads(request.body)
            email = data.get('email', '')

            # Vérifiez si l'utilisateur existe déjà
            users_collection = db_manager.get_users_collection()
            existing_user = users_collection.find_one({'email': email})

            if existing_user:
                return HttpResponse('L\'utilisateur existe déjà', status=400)

            # Créez un nouvel utilisateur
            new_user = {
                'nom': data.get('nom', ''),
                'prenom': data.get('prenom', ''),
                'email': email,
                'password': data.get('password', ''),
                'adresse': data.get('adresse', ''),
            }

            # Insérez l'utilisateur dans la base de données
            users_collection.insert_one(new_user)

            return HttpResponse('Utilisateur créé', status=201)

        except json.JSONDecodeError:
            return HttpResponse('Format JSON invalide', status=400)
    else:
        return HttpResponse('Requête invalide', status=405)

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            # Extrait les données JSON du corps de la requête
            data = json.loads(request.body)
            email = data.get('email', '')
            password = data.get('password', '')

            # Vous pouvez maintenant utiliser email et password pour vérifier l'authentification
            # Par exemple, recherchez l'utilisateur dans la base de données et comparez le mot de passe

            # Supposons que vous ayez une fonction pour vérifier l'authentification
            user_info = custom_authenticate(email, password)
            if user_info:
                return JsonResponse(user_info)  # Retourne les informations de l'utilisateur au format JSON
            else:
                return HttpResponse('Mot de passe incorrect', status=401)
            
        except json.JSONDecodeError:
            return HttpResponse('Format JSON invalide', status=400)
    else:
        return HttpResponse('Requête invalide', status=405)

def custom_authenticate(email, password):
    # Connexion à la base de données
    users_collection = db_manager.get_users_collection()

    # Recherchez l'utilisateur par email
    user = users_collection.find_one({'email': email})

    if user:
        # Si l'utilisateur est trouvé, comparez les mots de passe
        if user['password'] == password:
            # Authentification réussie, retournez les informations de l'utilisateur sous forme de JSON
            user_info = {
                'nom': user['nom'],
                'prenom': user['prenom'],
                'adresse': user['adresse'],
                'role': user.get('role', '')  # Assurez-vous que votre modèle d'utilisateur inclut le champ 'role'
            }
            return user_info  # Retourne les informations de l'utilisateur
    return None  # Authentification échouée

def pending_orders(request):
    # Connexion à la base de données MongoDB
    order_collection = db_manager.get_order_collection()

    # Recherche des commandes avec le statut "A livrer"
    pending_orders = list(order_collection.find({'statut': 'A livrer'}))

    # Convertir les données en JSON en utilisant json_util pour gérer les ObjectId
    data = {'pending_orders': json_util.dumps(pending_orders)}

    return JsonResponse(data, safe=False)