from random import randint
from Node import Node
import pickle as pickle
import socket, sys
import threading
import hashlib
import time
import uuid
import re


class Block:

    __maxTransactions = 10

    def __init__(self, prevBlockHash, id) -> None:

        self.__prevBlockHash = prevBlockHash
        self.__blockNumber = id
        self.__transactions = {}
        self.__merkelRoot = None
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
                return True

            else:
                return False
        else:
            pass

    def closeBlock(self):
        # if len(self.__transactions) == self.__maxTransactions:
        self.__blockHash = self.computeBlockHash()
        self.__nonce = self.computeNonce()
        self.__merkelRoot = self.computeMerkelRoot()
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
