import hashlib
import math


class Leaf:

    ## Position : 0 = Gauche, 1 = Droite
    ## Hauteur : 0 = feuille, N = Racine
    ## id : identifiant de la feuille, celle la plus a gauche = 0, ensuite 1, ensuite 2...
    def __init__(self, value, position, hauteur, id):

        self.value = value
        self.position = position
        self.hauteur = hauteur
        self.id = id