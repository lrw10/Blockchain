# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:15:51 2022

@author: Loba
"""

from random import randint
import socket, sys  # Import socket module
import threading
from Node import Node
import re


class Listen(threading.Thread):
    def __init__(self, miner):
        threading.Thread.__init__(self)
        self.miner = miner
        digit = "(1?[0-9]{1,2}|2[0-4][0-9]|25[0-5])"  # nombre de 0 à 255
        self.IpPattern = re.compile(
            "\('{}.{}.{}.{}', {}\)".format(digit, digit, digit, digit, "\d{1,5}")
        )  # pattern => (host, port)

    def run(self):  # reception

        while self.miner.node.run:
            try:
                """
                attente d'un message:
                cas 1 => data = -1 : c'est un ACK
                cas 2 => data = (host, port) : un nouveau voisin veut se connecter
                """
                try:
                    data, sender = self.miner.sock.recvfrom(1024)
                    self.processData(data, sender)
                except socket.timeout as e:
                    continue
            except socket.error as e:
                print(e)
                pass
        self.miner.sock.close()  # fermeture du lien

    def processData(self, data: bytes, sender: tuple):
        # ajout du nouveau voisin à la liste
        message = data.decode()
        senderHost = sender[0]
        senderPort = sender[1]
        if senderHost == self.miner.node.host:
            if senderPort == self.miner.node.port:
                return  # je ne prend pas en compte les messages envoyés à moi-même

        # si c'est un nouveau voisin
        if sender not in self.miner.node.miners:
            self.miner.node.miners.append(sender)
            if self.miner.node.miners != []:
                for host, port in self.miner.node.miners:
                    # j'informe mes voisins de l'arrivée du nouveau
                    self.miner.sock.sendto(
                        bytes(str(sender), "utf-8"),
                        (host, port),
                    )

        if message == "-1":
            return
        if message == "bye!":
            if sender in self.miner.node.miners:
                self.miner.node.miners.remove(sender)
                return
        else:
            self.processAddress(message)

        print("reveiced {} from {}".format(message, sender))

        # envoie d'un ACK => "-1"
        self.miner.sock.sendto(
            bytes("-1", "utf-8"),
            sender,
        )

    def processAddress(self, data: str):

        try:  # si le message est une addresse je l'enregiste
            if self.IpPattern.match(data):
                address = data.split(", ")
                host = self.cleanAddress(address[0])
                port = int(self.cleanAddress(address[1]))
                if (host, port) not in self.miner.node.miners and (
                    (host, port) != (self.miner.node.host, self.miner.node.port)
                ):
                    self.miner.node.miners.append((host, port))

                    self.sendMyneighbors()

        except Exception as e:
            print(e)

    def cleanAddress(self, addr: str):
        return re.sub("\(|\)|,|'| ", "", addr)

    def sendMyneighbors(self):
        if self.miner.node.miners != []:
            for neighbor in self.miner.node.miners:
                for host, port in self.miner.node.miners:
                    # j'informe mes voisins de l'arrivée du nouveau
                    self.miner.sock.sendto(bytes(str((host, port)), "utf-8"), neighbor)


class Actions(threading.Thread):
    def __init__(self, miner):
        threading.Thread.__init__(self)
        self.miner = miner

    def run(self):  # envoi

        while self.miner.node.run:

            action = input(">")

            if action == "v":
                print(self.miner.node.miners)

            # déconnection
            elif action == "s":
                try:
                    print("Close")

                    # si je suis connecté à des voisins
                    if self.miner.node.miners != []:
                        for host, port in self.miner.node.miners:
                            # je leur signal mon départ
                            self.miner.sock.sendto(bytes("bye!", "utf-8"), (host, port))

                    self.miner.node.run = False  # arret de la boucle

                except Exception as e:
                    print(e, "\n déconnection échoué.")

            elif action == "id":
                print(
                    " Host = ",
                    self.miner.node.host,
                    "\n",
                    "Port = ",
                    self.miner.node.port,
                    "\n",
                    "Id = ",
                    self.miner.node.id,
                )

            elif action == "connect":
                # je récupère l'adresse de le cible
                address = (input("Host:"), int(input("Port:")))
                try:
                    self.miner.sock.sendto(
                        bytes(input("Entrez un message: "), "utf-8"), address
                    )
                except socket.error as e:
                    print(e, "\nconnection échoué.")
            else:
                continue


class Miner:

    __type = "MINER"
    __timeout = 0.0000001

    def __init__(self, host=socket.gethostname(), port=1234):
        self.node = Node(host, port, self.__type)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.settimeout(self.__timeout)
        self.sock.bind((self.node.host, self.node.port))

    def run(self):
        L = Listen(self)
        A = Actions(self)
        L.start()
        A.start()


Miner = Miner(sys.argv[1], sys.argv[2])
Miner.run()
