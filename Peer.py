# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:15:51 2022

@author: Loba
"""

from email import message
from random import randint
import socket, sys  # Import socket module
import threading
import re


class Listen(threading.Thread):
    def __init__(self, peer):
        threading.Thread.__init__(self)
        self.peer = peer
        digit = "(1?[0-9]{1,2}|2[0-4][0-9]|25[0-5])"  # nombre de 0 à 255
        self.IpPattern = re.compile(
            "\('{}.{}.{}.{}', {}\)".format(digit, digit, digit, digit, "\d{1,5}")
        )  # pattern => (host, port)

    def run(self):  # reception

        while self.peer.condi:
            try:
                """
                attente d'un message:
                cas 1 => data = -1 : c'est un ACK
                cas 2 => data = (host, port) : un nouveau voisin veut se connecter
                """

                data, peer = self.peer.sock.recvfrom(1024)
                self.processData(data, peer)
            except socket.error as e:
                # sys.exit()
                print(e)
                pass
        self.peer.sock.close()  # fermeture du lien

    def processData(self, data: bytes, sender: str):
        # ajout du nouveau voisin à la liste
        message = data.decode()

        if sender not in self.peer.neigboors:
            if self.peer.neigboors != []:
                for host, port in self.peer.neigboors:
                    # j'informe mes voisins de l'arrivée du nouveau
                    self.peer.sock.sendto(
                        bytes(str(sender), "utf-8"),
                        (host, port),
                    )
            self.peer.neigboors.append(sender)
        else:

            if message == "-1":
                return
            if message == "bye!":
                if sender in self.peer.neigboors:
                    self.peer.neigboors.remove(sender)
                    return
            else:
                self.processAddress(message)

        print("reveiced {} from {}".format(message, sender))

        # envoie d'un ACK => "-1"
        self.peer.sock.sendto(
            bytes("-1", "utf-8"),
            self.peer.neigboors[-1],
        )

    def processAddress(self, data: str):

        try:  # si le message est une addresse je l'enregiste
            if self.IpPattern.match(data):
                address = data.split(", ")
                host = self.cleanAddress(address[0])
                port = int(self.cleanAddress(address[1]))
                if (host, port) not in self.peer.neigboors:
                    self.peer.neigboors.append((host, port))
        except Exception as e:
            print(e)

    def cleanAddress(self, addr: str):
        return re.sub("\(|\)|,|'| ", "", addr)


class Actions(threading.Thread):
    def __init__(self, peer):
        threading.Thread.__init__(self)
        self.peer = peer

    def run(self):  # envoi

        while self.peer.condi:

            action = input(">")

            if action == "v":
                print(self.peer.neigboors)

            # déconnection
            elif action == "s":
                try:
                    print("Close")

                    # si je suis connecté à des voisins
                    if self.peer.neigboors != []:
                        for host, port in self.peer.neigboors:
                            # je leur signal mon départ
                            self.peer.sock.sendto(bytes("bye!", "utf-8"), (host, port))

                    self.peer.condi = False  # arret de la boucle

                except Exception as e:
                    print(e, "\n déconnection échoué.")

            elif action == "id":
                print("Host = ", self.peer.host, "\n", "Port = ", self.peer.port, "\n")

            elif action == "connect":
                # je récupère l'adresse de le cible
                address = (input("Host:"), int(input("Port:")))
                try:
                    self.peer.sock.sendto(
                        bytes(input("Entrez un message: "), "utf-8"), address
                    )
                except socket.error as e:
                    print(e, "\nconnection échoué.")
            else:
                continue


class Peer:
    def __init__(self, host=socket.gethostname(), port=1234, name=None):
        self.host = host
        self.port = port
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.settimeout(10)
        self.sock.bind((self.host, int(self.port)))
        self.neigboors = []
        self.condi = True  # condition boucle infinie

    def run(self):
        L = Listen(self)
        A = Actions(self)
        L.start()
        A.start()


Peer = Peer(sys.argv[1], sys.argv[2])
Peer.run()
