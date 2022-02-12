from Node import Node
from random import randint
import socket, sys
import pickle as pickle
import threading
import time
import uuid
import re


class Block:
    __blockHash = None
    __prevBlockHash = -1
    __nonce = None
    __time = time.time()
    __merkelRoot = None
    __maxTransactions = 10
    __transactions = {}

    def __init__(self, prevBlockHash) -> None:
        self.prevBlockHash = prevBlockHash

    def getBlockHash(self):
        if self.__blockHash:
            return self.__blockHash
        else:
            return None

    def getPrevBlockHash(self):
        return self.__prevBlockHash

    def getNonce(self):
        if self.__nonce:
            return self.__nonce
        else:
            return None

    def getTime(self):
        return self.__time

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

    def addTransaction(self, transaction):
        if transaction not in self.__transactions:
            if len(self.__transactions) < self.__maxTransactions:
                self.__transactions[transaction] = transaction
                return True

            else:
                return False
        else:
            pass

    def closeBlock(self):
        if len(self.__transactions) == self.__maxTransactions:
            self.__blockHash = self.computeBlockHash()  # calculer le hash du block
            self.__nonce = self.computeNonce()
            self.__merkelRoot = self.computeMerkelRoot()
