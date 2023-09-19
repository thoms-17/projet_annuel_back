from django.db import models

class Utilisateur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    adresse = models.TextField()
    password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.prenom} {self.nom}"
