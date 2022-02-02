# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:15:51 2022

@author: Loba
"""

from random import randint
import socket, sys  # Import socket module
import threading
import time


class Listen(threading.Thread):
    def __init__(self, peer):
        threading.Thread.__init__(self)
        self.peer = peer

    def run(self):  # reception

        while self.peer.condi:
            try:
                # FERMER CHAQUE CONNEXION OUVERTE

                """
                attente d'un message:
                cas 1 => data = -1 : c'est un ACK
                cas 2 => data = autre : un nouveau voisin veut se connecter
                """
                data, peer = self.peer.sock.recvfrom(1024)
                # ajout du nouveau voisin à la liste
                if peer not in self.peer.neigboors:
                    self.peer.neigboors.append(peer)

                message = data.decode()
                if message == "-1":
                    continue
                if message == "bye!":
                    if peer in self.peer.neigboors:
                        self.peer.neigboors.remove(peer)
                    continue
                print("reveiced {} from {}".format(message, peer))

                # envoie d'un ACK => "-1"
                self.peer.sock.sendto(
                    bytes("-1", "utf-8"),
                    self.peer.neigboors[-1],
                )
            except socket.error as e:
                # sys.exit()
                print(e)
                pass


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
                    self.peer.condi = False  # arret de la boucle
                    # si je suis connecté à des voisins
                    if self.peer.neigboors != []:
                        for host, port in self.peer.neigboors:
                            # je leur signal mon départ
                            print(
                                self.peer.sock.sendto(
                                    bytes(action, "utf-8"), (host, port)
                                )
                            )
                    self.peer.sock.close()  # fermeture du lien
                    sys.exit()  # arret du programme
                except Exception as e:
                    print(e, "\n déconnection échoué.")

            elif action == "id":
                print("Host = ", self.peer.host, "\n", "Port = ", self.peer.port, "\n")

            elif action == "connect":
                # je récupère l'adresse de le cible
                address = (input("Host:"), int(input("Port:")))
                try:
                    print(
                        self.peer.sock.sendto(
                            bytes(input("Entrez un message: "), "utf-8"), address
                        )
                    )
                except socket.error as e:
                    print(e, "\nconnection échoué.")
            else:
                print("che ne compwen paa")
                continue


class Peer:
    def __init__(self, host, port, name=None):
        self.host = host
        self.port = port
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
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
