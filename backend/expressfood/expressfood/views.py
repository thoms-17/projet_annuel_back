import random
import os
import json

from datetime import datetime
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
        return self.db['commande']


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


def all_order(request):
    order_collection = db_manager.get_order_collection()
    order_list = list(order_collection.find({}))
    data = {'order': json_util.dumps(order_list)}
    return JsonResponse(data, safe=False)


@csrf_exempt
def order(request):
    global current_order_number

    if request.method == 'GET':

        order_collection = db_manager.get_order_collection()
        order_data = list(order_collection.find({}))

        order = []

        for order_item in order_data:
            order.append({
                'numero_commande': order_item['numero_commande'],
                'plat': order_item['plat'],
                'adresse_livraison': order_item['adresse_livraison'],
            })

        return JsonResponse({'order': order})

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))

        selected_items = data.get('selectedItems', [])

        adresse_livraison = data.get('adresse_livraison', '')
        nom_client = data.get('nom_client', '')

        order_items = []

        for item in selected_items:
            nom = item.get('nom', '')
            prix = item.get('prix', 0.0)

            order_items.append({
                'nom': nom,
                'prix': prix,
            })

        numero_commande = current_order_number
        heure_commande = datetime.now().isoformat()

        new_order = {
            'numero_commande': numero_commande,
            'plat': order_items,
            'adresse_livraison': adresse_livraison,
            'heure_commande': heure_commande,
            'statut': 'A livrer',
            'nom_client': nom_client,
        }

        order_collection = db_manager.get_order_collection()
        result = order_collection.insert_one(new_order)

        response_data = {
            'numero_commande': str(result.inserted_id),
            'message': 'Commande créée avec succès.'
        }
        current_order_number += 1

        return JsonResponse(response_data, status=201)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


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

            user_info = custom_authenticate(email, password)
            if user_info:
                return JsonResponse(user_info)
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
                'role': user.get('role', '')
            }
            return user_info
    return None  # Authentification échouée


def pending_orders(request):
    # Connexion à la base de données MongoDB
    order_collection = db_manager.get_order_collection()

    pending_orders = list(order_collection.find({'statut': 'A livrer'}))

    # Convertir les données en JSON en utilisant json_util pour gérer les ObjectId
    data = {'pending_orders': json_util.dumps(pending_orders)}

    return JsonResponse(data, safe=False)


def daily_special(request):

    daily_special_collection = db_manager.get_meal_collection()
    daily_special_data = list(daily_special_collection.find({}))

    daily_special = []

    for meal_data in daily_special_data:
        meal_dict = {
            'nom': meal_data['nom'],
            'description': meal_data['description'],
            'prix': meal_data['prix'].to_decimal(),
            'type': meal_data['type'],
        }
        daily_special.append(meal_dict)

    return JsonResponse({'daily_special': daily_special})


current_order_number = 1

@csrf_exempt
def prendre_en_charge(request):

    try:
        # Connexion à la base de données MongoDB
        commandes_collection = db_manager.get_order_collection()

        data = json.loads(request.body.decode('utf-8'))

        numero_commande = data.get('numero_commande', '')

        result = commandes_collection.update_one(
            {'numero_commande': numero_commande},
            {'$set': {'statut': 'En cours de livraison'}}
        )

        if result.modified_count > 0:
         return JsonResponse({'message': 'Statut mis à jour avec succès'}, status=200)
        else:
            return JsonResponse({'message': 'Aucune commande trouvée avec ce numéro de commande'}, status=404)


    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
    
@csrf_exempt
def livraison_terminee(request):

    try:
        # Connexion à la base de données MongoDB
        commandes_collection = db_manager.get_order_collection()

        data = json.loads(request.body.decode('utf-8'))

        numero_commande = data.get('numero_commande', '')

        result = commandes_collection.update_one(
            {'numero_commande': numero_commande},
            {'$set': {'statut': 'Livraison terminée'}}
        )

        if result.modified_count > 0:
         return JsonResponse({'message': 'Statut mis à jour avec succès'}, status=200)
        else:
            return JsonResponse({'message': 'Aucune commande trouvée avec ce numéro de commande'}, status=404)


    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def create_meal(request):
    try:
        # Accédez à la collection des plats dans MongoDB
        meals_collection = db_manager.get_meal_collection()

        # Récupérez les données du plat à partir de la requête POST
        data = request.POST
        print(data)
        nom = data.get('nom', '')
        description = data.get('description', '')
        prix = data.get('prix', 0.0)
        type = data.get('type', '')

        # Créez un nouveau plat
        nouveau_plat = {
            'nom': nom,
            'description': description,
            'prix': prix,
            'type': type
        }

        # Insérez le nouveau plat dans la collection des plats
        result = meals_collection.insert_one(nouveau_plat)

        if result.inserted_id:
            return JsonResponse({'message': 'Plat créé avec succès'}, status=201)
        else:
            return JsonResponse({'message': 'Échec de la création du plat'}, status=500)
    
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)