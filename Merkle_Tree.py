### Merkle tree ###

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


class MerkleTree:

    def __init__(self):
        
        self.merkleRoot = 0
        self.tree = []
        self.hauteur_arbre = 0
        self.nbLeaf = 0

    def print_Tree(self):
        h = self.hauteur_arbre
        for i in self.tree[::-1]:
            if i.hauteur != h:
                print("\n")
                h = i.hauteur
            print("hauteur: ", i.hauteur)
            print("Value: ", i.value)
            print("position: ", i.position)
            print("id: ", i.id)


## Etant donné une feuille, on retrouve la merkle root de l'arbre connu par le bloc 
## True si merkleroot calculé = merkle root de l'arbre en mémoire
def MerkleProof(merkleTree, leaf):
    position = leaf.position
    id = leaf.id
    h = 0
    val = leaf.value

    ## On continue jusqu'à arriver à la racine
    while h != merkleTree.hauteur_arbre:
        ### Si nombre de feuille est pair (pas de problème), mais ATTENTION, on peut avoir 6 feuilles (nb pair) mais on aura à la hauteur 1 -> 3 noeud..
        if merkleTree.nbLeaf % 2 == 0: 
            ## Si position de la feuille est gauche, on regarde le voisin de droite, sinon inverse
            ### id de la nouvelle feuille = (id feuille de gauche / 2) + nombre de noeud (arrondi au superieur)

            ##Si je suis sur un noeud de gauche, je vérifie que le noeud suivant est bien à ma hauteur sinon je garde la même valeur
            if position == 0:
                voisin = merkleTree.tree[id + 1]
                if voisin.hauteur == h:
                    val = val + voisin.value

                    id = math.ceil((id / 2) + merkleTree.nbLeaf)
                else:
                    val = val
                    id = math.ceil((id / 2) + merkleTree.nbLeaf)

            else: 
                voisin = merkleTree.tree[id - 1]
                val = val + voisin.value

                id = math.ceil(((id-1) / 2) + merkleTree.nbLeaf)


            print(id)
            h += 1
            position = merkleTree.tree[id].position

        ### Si nombre de feuille est impair...
        else:
            ## Si je suis sur un noeud de gauche, je vérifie que le voisin de droite est à ma hauteur sinon je garde la même valeur
            if position == 0:
                voisin = merkleTree.tree[id + 1]
                if voisin.hauteur == h:
                    val = val + voisin.value

                    id = math.ceil((id / 2) + merkleTree.nbLeaf)
                else:
                    val = val
                    id = math.ceil((id /  2) + merkleTree.nbLeaf)
            ## Sinon pas de problème
            else:
                voisin = merkleTree.tree[id - 1]
                val = val + voisin.value

                id = math.ceil(((id - 1) / 2) + merkleTree.nbLeaf)

            print(id)
            h += 1
            position = merkleTree.tree[id].position


    if val == merkleTree.merkleRoot:
        return True
    else: 
        return False

    
### Creation de l'arbre de merkle grace à une liste de transaction
'''
merkleTree: arbre qui est génére, vide au début
transactions: liste de transactions, liste de STRING ou d'ENTIER
firstIter: True au début
id: entier
'''
def create_Tree(merkleTree, transactions, firstIter, id):
    #### Stop
    if len(transactions) == 1:
        merkleTree.merkleRoot = transactions[0].value
        merkleTree.hauteur_arbre = transactions[0].hauteur
        return None

    if firstIter == True:
        tree_tmp = []
        pos = 0

        for i in transactions:
            hashed_leaf = hash(i)

            leaf = Leaf(hashed_leaf, (pos % 2), 0, pos)

            merkleTree.tree.append(leaf)
            tree_tmp.append(leaf)

            merkleTree.nbLeaf += 1

            pos += 1

        create_Tree(merkleTree, tree_tmp, False, pos)
    

    else:
        tree_tmp = []

        ### Nombre pair de feuille
        if len(transactions) % 2 == 0:
            hauteur = transactions[0].hauteur + 1
            pos = 0
            for i in range(0, len(transactions), 2):

                val = transactions[i].value + transactions[i+1].value

                leaf = Leaf(val, (pos % 2), hauteur, id)

                merkleTree.tree.append(leaf)
                tree_tmp.append(leaf)

                pos += 1
                id += 1
                
                
        else: 
            hauteur = transactions[0].hauteur + 1
            pos = 0
            for i in range(0, len(transactions) - 1, 2):
                val = transactions[i].value + transactions[i+1].value

                leaf = Leaf(val, (pos % 2), hauteur, id)

                merkleTree.tree.append(leaf)
                tree_tmp.append(leaf)

                pos += 1
                id += 1
                
            ### Ajout du dernier element si impair avec hauteur += 1
            leaf = Leaf(transactions[-1].value, pos % 2, hauteur, id)
            tree_tmp.append(leaf)
            merkleTree.tree.append(leaf)
            id += 1
            # tree_tmp.append(transactions[-1])
            # merkleTree.tree.append(transactions[-1])

        create_Tree(merkleTree, tree_tmp, False, id)




test = MerkleTree()

#transac = ["0", "1", "2"]
#transac = ["0", "1", "3", "4"]
transac = ["0", "1", "3", "4", "5", "6", "7"]
#transac = ["0", "1", "3", "4", "5", "6", "7", "8", "9", "10"]

create_Tree(test, transac, True, 0)

print("Merkle Root: ", test.merkleRoot)
print("Hauteur arbre: ", test.hauteur_arbre)
print("\n")
print("Merkle Tree: ")
test.print_Tree()


x = test.tree[2]

print("\n")
print(x)

proof = MerkleProof(test, x)

print(proof)