from abc import ABC, abstractmethod
import uuid
import socket, sys  # Import socket module
import threading
import re


class Node(object):
    def __init__(self, host, port, type=None) -> None:
        self.host = host
        self.port = int(port)
        self.miners = []
        self.wallets = []
        self.id = uuid.uuid4()
        self.type = type
        self.run = True
