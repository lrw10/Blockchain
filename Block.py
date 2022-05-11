from random import randint
from Node import Node
import pickle as pickle
import socket, sys
import threading
import hashlib
import time
import uuid
import re
import math
from Leaf_merkleTree import Leaf
from Merkle_Tree import MerkleTree


class Block:

    __maxTransactions = 10

    def __init__(self, prevBlockHash, id) -> None:

        self.__prevBlockHash = prevBlockHash
        self.__blockNumber = id
        self.__transactions = {}
        self.__merkelRoot = None
        self.__merkleTree = None
        # self.__time = None  # time.time()
        self.__nonce = None
        self.__blockHash = None
        self.__noncePattern = "0xd"

    def getBlockHash(self):
        if self.__blockHash:
            return self.__blockHash
        else:
            return None

    def getPrevBlockHash(self):
        return self.__prevBlockHash

    def setPrevBlockHash(self, prevBlockHash):
        self.__prevBlockHash = prevBlockHash

    def getNonce(self):
        if self.__nonce:
            return self.__nonce
        else:
            return None

    # def getTime(self):
    #     return self.__time

    def getMerkelRoot(self):
        if self.__merkelRoot:
            return self.__merkelRoot
        else:
            return None

    def getTransactions(self):
        return self.__transactions

    def getMaxTransactions(self):
        return self.__maxTransactions

    def setMaxTransactions(self, newValue):
        self.__maxTransactions = newValue

    def getBlockNumber(self):
        return self.__blockNumber

    def setBlockNumber(self, num):
        self.__blockNumber = num

    def addTransaction(self, transaction):

        if transaction.getId() not in self.__transactions:
            # if I have enougth place to add a transaction I add it
            if len(self.__transactions) < self.__maxTransactions:
                self.__transactions[transaction.getId()] = self.strToHex(
                    hashlib.sha256(pickle.dumps(transaction)).digest().hex()
                )
                return "OK"

            else:
                return "OK but in next block"
        else:
            return "not OK"

    def closeBlock(self):
        # if len(self.__transactions) == self.__maxTransactions:
        self.__blockHash = self.computeBlockHash()
        self.__nonce = self.computeNonce()
        self.__merkelRoot = self.computeMerkelRoot()
        if self.__blockNumber != -1:
            print("Compute Merkle Root...")
            self.computeMerkleTree()
            print("Merkle Root: ", self.__merkelRoot)
            #self.printTree()
        # self.__time = None  # time.time()

    def computeBlockHash(self):
        """compute the blockHash of the current block

        --------
        Returns
            The sha256 hash of the current block in hexadecimal format
        """

        return self.strToHex(
            hashlib.sha256(pickle.dumps(self.__transactions)).digest().hex()
        )

    def computeNonce(self):
        """compute a hexadecimal value that verify self.__noncePattern constraint by multiplication with self.__blockHash

        --------
        Returns
            Hexadecimal
        """
        nonce = hex(1)
        print("Comput Nonce ...")
        while not self.valideNonce(nonce):

            nonce = self.intToHex(
                self.hexToInt(nonce) * self.hexToInt(self.__blockHash)
            )

            # print((nonce))
            self.valideNonce(nonce)
        return nonce

    def valideNonce(self, nonce):
        """verify if self.__noncePattern is satisfied

        --------
        Returns
            Bool
        """
        for i in range(len(self.__noncePattern)):
            if nonce[i] != self.__noncePattern[i]:
                return False

        return True

    def strToHex(self, strValue):
        return hex(int(strValue, 16))

    def hexToInt(self, hexValue):
        return int(hexValue, 16)

    def intToHex(self, intValue):
        return hex(intValue)

    def computeMerkelRoot(self):
        return "MKLR"
    
    def computeMerkleTree(self):
        self.__merkleTree = MerkleTree()
        
        self.__merkleTree.create_Tree(self.__transactions, True, 0)
        self.__merkelRoot = self.__merkleTree.merkleRoot
        
    def printTree(self):
        print("\n")
        self.__merkleTree.print_Tree()
        print("\n")
        
    """
    Compute MerkleProof
    """
    def checkTransaction(self, id):
        id = uuid.UUID(id)
        try:
            transaction = self.__transactions[id]
        except Exception as e:
            print("Transaction Inconnue")
            return
        print("\n Merkle Proof from Transaction : ", transaction)
        
        bool, proof = self.__merkleTree.MerkleProof(transaction)
        
        print("\n Résultat test: ", bool)
        print("Preuve: ", proof)
        print("\n")
        x = self.__merkleTree.testProof(proof, transaction)
        
        return x