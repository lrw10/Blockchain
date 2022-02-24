# -*- coding: utf-8 -*- 
   
from ctypes.wintypes import PLONG
from Node import Node
import pickle as pickle
import socket, sys
import threading
import uuid
import re
import time
#from ping3 import ping


class PingActions(threading.Thread):
    def __init__(self, miner):
        threading.Thread.__init__(self)
        self.miner = miner

    def run(self):
        """
        Listen keyboard
        """
        while self.miner.node.run:

            time.sleep(10)
            neighbors_copy = neighbors_copy = self.miner.neighbors.copy()

            if not neighbors_copy: 
                continue
            else:
                for id, neighbor in neighbors_copy.items():
                    # I say bye to my neighbors
                    deconnectionMessage = ("Ping", self.miner.node.id, self.miner.node.host, self.miner.node.port)
                    self.miner.pinged = neighbor.id

                    self.miner.sock.sendto(self.miner.serialize(deconnectionMessage), (neighbor.host, neighbor.port), )

                    #time.sleep(10)

                    # try : 
                    #     try:
                    #         data, sender = self.miner.sock.recvfrom(1024)
                    #         receivedmessage = self.miner.deserialize(data)
                    #         if receivedmessage[0] == "Pong" and receivedmessage[1] == id:
                    #             continue
                    #         else: print('wtf')
            
                    #     except socket.timeout as e:
                    #         #del self.miner.neighbors[neighbor.id]
                    #         continue
    
                    # except socket.error as e:
                    #     print(id, "ne répond plus")
                    #     del self.miner.neighbors[neighbor.id]
                    #     pass


class Listen(threading.Thread):
    def __init__(self, miner):
        threading.Thread.__init__(self)
        self.miner = miner
        __digit = "(1?[0-9]{1,2}|2[0-4][0-9]|25[0-5])"  # nombre de 0 à 255
        self.__IpPattern = re.compile(
            "\('{}.{}.{}.{}', {}\)".format(
                __digit, __digit, __digit, __digit, "\d{1,5}"
            )
        )  # pattern => (host, port)

    def run(self):
        """
        Process received messages
        """

        while self.miner.node.run:
            try:
                """
                possible messages:
                case 1 => data = Node : new neighbor
                case 2 => data = "bye!" : deconnection message
                case 3 => data = (str, UUID) : it is an ACK
                """
                try:
                    # wait for new message
                    data, sender = self.miner.sock.recvfrom(1024)
                    # ignore self sended messages
                    if not self.sendToMyself(sender):
                        self.processData(data, sender)
                    else:
                        continue
                except socket.timeout as e:
                    continue
            ### Arrive quand on envoie un message à qqn qui n'existe pas avec la classe PingActions
            except socket.error as e:
                print(self.miner.pinged, "ne répond plus")
                del self.miner.neighbors[self.miner.pinged]
                pass
        self.miner.sock.close()  # close the link

    def processData(self, data: bytes, sender: tuple):
        """Process received data.

        Parameters
        ----------
        graph :
        data : bytes encoded message
        sender : tuple
            the sender address
        """
        try:

            receivedNode = self.miner.deserialize(data)
            # Is it a Node?
            if isinstance(receivedNode, Node):
                if receivedNode.type == "MINER":
                    self.processMiner(receivedNode, sender)
                elif receivedNode.type == "WALLET":
                    pass

            # Is it a response?
            elif (
                isinstance(receivedNode, tuple)
                and isinstance(receivedNode[0], str)
                and isinstance(receivedNode[1], uuid.UUID)
            ):
                if receivedNode[0] == "bye!":
                    # If I know the sender I delete it
                    if receivedNode[1] in self.miner.neighbors:
                        del self.miner.neighbors[receivedNode[1]]
                        print("reveiced {} from {}".format(receivedNode, sender))
                #elif receivedNode[0] == "Ping":
                #    m = ("Pong", self.miner.node.id)
                #    self.miner.sock.sendto(self.miner.serialize(m), (receivedNode[2], receivedNode[3]), )
                else:
                    pass
                if receivedNode[0] != "Ping" and receivedNode[0] != "Pong":
                    print("reveiced {} from {}".format(receivedNode, sender))
        
        except Exception as e:
            print("Other_Pickel_Error", e)
            pass

        return

    def sendToMyself(self, address):
        """Verify is the sender is the current node.

        Parameter
        ----------
        address : tuple
            the sender's address

        Returns
        -------
        bool
            True if the sender is the current node
        """
        return address == (self.miner.node.host, self.miner.node.port)

    def processMiner(self, node, sender):
        """Process Miner information

        Parameter
        ----------
        node : Node object
        sender: tuple
        """
        # new neighbor ?
        if node.id not in self.miner.neighbors:
            # I send my new neighbor to my neighbors
            for id, neighbor in self.miner.neighbors.items():
                self.miner.sock.sendto(
                    self.miner.serialize(node),
                    (neighbor.host, neighbor.port),
                )

                # I send my neighbors to my new neighbor
                self.miner.sock.sendto(
                    self.miner.serialize(neighbor),
                    (node.host, node.port),
                )

            # I add my new neighbor to my neighbor list
            self.miner.neighbors[node.id] = node
            # send an "ACK" => self.miner.node
            self.miner.sock.sendto(
                self.miner.serialize(self.miner.node),
                sender,
            )


class Actions(threading.Thread):
    def __init__(self, miner):
        threading.Thread.__init__(self)
        self.miner = miner

    def run(self):
        """
        Listen keyboard
        """
        while self.miner.node.run:

            action = input(">")

            # neighbors
            if action == "v":
                print(self.miner.neighbors)

            # deconnexion
            elif action == "exit":
                self.deconnection()

            elif action == "id":
                print(
                    "Host = ",
                    self.miner.node.host,
                    "\n",
                    "Port = ",
                    self.miner.node.port,
                    "\n",
                    "Id = ",
                    self.miner.node.id,
                    "\n",
                    "Type = ",
                    self.miner.node.type,
                )

            elif action == "test":
                pass

            elif action == "connect":
                self.connection()

            elif action == "STOP":
                self.miner.node.run = False
            else:
                continue

    def connection(self):
        """
        Send connection request
        """
        # Ask the address of the target node
        address = (input("Host:"), int(input("Port:")))
        try:
            # Send a connection request
            self.miner.sock.sendto(
                self.miner.serialize(self.miner.node),
                address,
            )
        except socket.error as e:
            print(e, "\nconnection failed.")

    def deconnection(self):
        """
        Stop the socket, the thread and send deconnection message to neighbors
        """
        try:
            for id, neighbor in self.miner.neighbors.items():
                # I say bye to my neighbors
                deconnectionMessage = ("bye!", self.miner.node.id)

                self.miner.sock.sendto(
                    self.miner.serialize(deconnectionMessage),
                    (neighbor.host, neighbor.port),
                )

            self.miner.node.run = False  # stop runnig
            print("Close")

        except Exception as e:
            print(e, "\n deconnection failed.")
            sys.exit()


class Miner:

    __type = "MINER"
    __timeout = 0.0000001

    def __init__(self, host=socket.gethostname(), port=1234):
        self.node = Node(host, port, self.__type)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.settimeout(self.__timeout)
        self.sock.bind((self.node.host, self.node.port))
        self.pinged = 0
        self.neighbors = {}
        self.wallets = {}

    def run(self):
        L = Listen(self)
        A = Actions(self)
        P = PingActions(self)
        L.start()
        A.start()
        P.start()

    def serialize(self, node):
        """Transform Node object into bytes

        Parameter
        ----------
        node : Node object

        Returns
        -------
        bytes
            The serialized Node
        """
        return pickle.dumps(node)

    def deserialize(self, serialized: bytes):
        """Transform bytes into an object

        Parameter
        ----------
        serialize : bytes

        Returns
        -------
        deserialize result
        """
        return pickle.loads(serialized)


Miner = Miner(sys.argv[1], sys.argv[2])
Miner.run()
