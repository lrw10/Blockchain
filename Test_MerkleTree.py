### Merkle tree ###

import hashlib
import math
from Leaf_merkleTree import Leaf

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
    
    def find_leaf(self, val):
        for i in range(self.nbLeaf):
            if val == self.tree[i].value:
                return self.tree[i]
        return 0


    ## Etant donné une feuille, on retrouve la merkle root de l'arbre connu par le bloc 
    ## True si merkleroot calculé = merkle root de l'arbre en mémoire + chemin (preuve)
    def MerkleProof(self, leaf):
        
        position = leaf.position
        id = leaf.id
        h = 0
        val = leaf.value
        proof = []

        ## On continue jusqu'à arriver à la racine
        while h != self.hauteur_arbre:
            ### Si nombre de feuille est pair (pas de problème), mais ATTENTION, on peut avoir 6 feuilles (nb pair) mais on aura à la hauteur 1 -> 3 noeud..
            if self.nbLeaf % 2 == 0: 
                ## Si position de la feuille est gauche, on regarde le voisin de droite, sinon inverse
                ### id de la nouvelle feuille = (id feuille de gauche / 2) + nombre de noeud (arrondi au superieur)

                ##Si je suis sur un noeud de gauche, je vérifie que le noeud suivant est bien à ma hauteur sinon je garde la même valeur
                if position == 0:
                    voisin = self.tree[id + 1]
                    if voisin.hauteur == h:
                        val = val + voisin.value

                        id = math.ceil((id / 2) + self.nbLeaf)
                    else:
                        val = val
                        id = math.ceil((id / 2) + self.nbLeaf)

                else: 
                    voisin = self.tree[id - 1]
                    val = val + voisin.value

                    id = math.ceil(((id-1) / 2) + self.nbLeaf)

                proof.append(voisin.value)
                h += 1
                position = self.tree[id].position

            ### Si nombre de feuille est impair...
            else:
                ## Si je suis sur un noeud de gauche, je vérifie que le voisin de droite est à ma hauteur sinon je garde la même valeur
                if position == 0:
                    voisin = self.tree[id + 1]
                    if voisin.hauteur == h:
                        val = val + voisin.value

                        id = math.ceil((id / 2) + self.nbLeaf)
                    else:
                        val = val
                        id = math.ceil((id /  2) + self.nbLeaf)
                ## Sinon pas de problème
                else:
                    voisin = self.tree[id - 1]
                    val = val + voisin.value

                    id = math.ceil(((id - 1) / 2) + self.nbLeaf)

                proof.append(voisin.value)
                h += 1
                position = self.tree[id].position


        if val == self.merkleRoot:
            return True, proof
        else: 
            return False, proof
        
        
    ## Test a partir d'un chemin et d'une feuille qu'on retombe sur la root
    def testProof(self, proof, leaf):
        for i in proof[::-1]: 
            leaf = leaf + i
        print("Merkle root trouvée: ", leaf, "et merkle root: ", self.merkleRoot)
        
        if leaf == self.merkleRoot: 
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
    def create_Tree(self, transactions, firstIter, id):
        #### Stop
        if len(transactions) == 1:
            self.merkleRoot = transactions[0].value
            self.hauteur_arbre = transactions[0].hauteur
            return None

        if firstIter == True:
            tree_tmp = []
            pos = 0

            for i in transactions:
                hashed_leaf = hashlib.sha256(i.encode('ascii')).hexdigest()
                hashed_leaf = hexToInt(hashed_leaf)
                
                leaf = Leaf(hashed_leaf, (pos % 2), 0, pos)

                self.tree.append(leaf)
                tree_tmp.append(leaf)

                self.nbLeaf += 1

                pos += 1

            self.create_Tree(tree_tmp, False, pos)
        

        else:
            tree_tmp = []

            ### Nombre pair de feuille
            if len(transactions) % 2 == 0:
                hauteur = transactions[0].hauteur + 1
                pos = 0
                for i in range(0, len(transactions), 2):

                    val = transactions[i].value + transactions[i+1].value

                    leaf = Leaf(val, (pos % 2), hauteur, id)

                    self.tree.append(leaf)
                    tree_tmp.append(leaf)

                    pos += 1
                    id += 1
                    
                    
            else: 
                hauteur = transactions[0].hauteur + 1
                pos = 0
                for i in range(0, len(transactions) - 1, 2):
                    val = transactions[i].value + transactions[i+1].value

                    leaf = Leaf(val, (pos % 2), hauteur, id)

                    self.tree.append(leaf)
                    tree_tmp.append(leaf)

                    pos += 1
                    id += 1
                    
                ### Ajout du dernier element si impair avec hauteur += 1
                leaf = Leaf(transactions[-1].value, pos % 2, hauteur, id)
                tree_tmp.append(leaf)
                self.tree.append(leaf)
                id += 1
                # tree_tmp.append(transactions[-1])
                # merkleTree.tree.append(transactions[-1])

            self.create_Tree(tree_tmp, False, id)
            
    

def hexToInt(hexValue):
        return int(hexValue, 16)


test = MerkleTree()

#transac = ["0", "1", "2"]
#transac = ["0", "1", "3", "4"]
#transac = ["0", "1", "3", "4", "5", "6", "7"]
transac = ["0", "1", "3", "4", "5", "6", "7", "8", "9", "10"]

test.create_Tree(transac, True, 0)

print("Merkle Root: ", test.merkleRoot)
print("Hauteur arbre: ", test.hauteur_arbre)
print("\n")
print("Merkle Tree: ")
test.print_Tree()


x = test.tree[0]

print("\n")
print(x)

proof, ids = test.MerkleProof(x)

print(proof)

print(test.testProof(ids, x.value))