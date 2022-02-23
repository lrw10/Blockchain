import uuid
import socket, sys  # Import socket module
import threading
import re


class Transaction(object):
    def __init__(self, sender, receiver, amount) -> None:

        self.__sender = sender
        self.__receiver = receiver
        self.__amount = amount
        self.__id = uuid.uuid4()

    def getId(self):
        return self.__id

    def getSender(self):
        return self.__sender

    def getReceiver(self):
        return self.__receiver

    def getAmount(self):
        return self.__amount
