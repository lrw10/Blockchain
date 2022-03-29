# -*- coding: utf-8 -*-
import traceback
from Transaction import Transaction
from Node import Node
from Block import Block
import pickle as pickle
import socket, sys
import threading
import uuid
import re
import time


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
                    data, sender = self.miner.sock.recvfrom(8192)
                    # ignore self sended messages
                    if not self.sendToMyself(sender):
                        self.processData(data, sender)
                    else:
                        continue
                except socket.timeout as e:
                    continue
            except socket.error as e:
                print("Socket_ERROR", e)
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
                    self.processWallet(receivedNode, sender)
            # Is it a Block?
            if isinstance(receivedNode, Block):
                if len(self.miner.blockchain) == 0:
                    self.miner.blockchain.append(receivedNode)
                elif (
                    receivedNode.getBlockNumber()
                    > self.miner.blockchain[-1].getBlockNumber()
                ):
                    self.miner.blockchain[-1] = receivedNode
                else:
                    pass
            # Is it a Transaction?
            elif isinstance(receivedNode, Transaction):
                self.broadcast(receivedNode, sender)

            # Is it a message?
            elif (
                isinstance(receivedNode, tuple)
                and isinstance(receivedNode[0], str)
                and isinstance(receivedNode[1], uuid.UUID)
            ):
                if receivedNode[0] == "bye!":
                    # If I know the sender I delete it
                    if receivedNode[1] in self.miner.miners:
                        del self.miner.miners[receivedNode[1]]
                    elif receivedNode[1] in self.miner.wallets:
                        del self.miner.wallets[receivedNode[1]]

            print("reveiced {} from {}".format(receivedNode, sender))

        except Exception as e:
            print("Other_Pickel_Error", e)
            traceback.print_exc()
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

    def processMiner(self, miner, sender):
        """Process Miner information

        Parameter
        ----------
        miner : Node object
        sender: tuple
        """
        # new neighbor ?
        if miner.id not in self.miner.miners:
            # I send my new neighbor to my neighbors
            for id, neighbor in self.miner.miners.items():
                self.miner.sock.sendto(
                    self.miner.serialize(miner),
                    (neighbor.host, neighbor.port),
                )

                # I send my neighbors to my new neighbor
                self.miner.sock.sendto(
                    self.miner.serialize(neighbor),
                    (miner.host, miner.port),
                )

            # I add my new neighbor to my neighbor list
            self.miner.miners[miner.id] = miner
            # send an "ACK" => self.miner.node
            self.miner.sock.sendto(
                self.miner.serialize(self.miner.node),
                sender,
            )

    def processWallet(self, wallet, sender):
        """Process Wallet information

        Parameter
        ----------
        wallet : Node object
        sender: tuple
        """
        # new neighbor ?
        if wallet.id not in self.miner.wallets:

            # I add my new neighbor to my neighbor list
            self.miner.wallets[wallet.id] = wallet
            # send an "ACK" => self.miner.node
            self.miner.sock.sendto(
                self.miner.serialize(self.miner.node),
                sender,
            )

    def broadcast(self, message, sender):
        """Broadcast messages from wallets and build blocks

        Parameter
        ----------
        message : tuple
        sender: tuple
        """
        #############self.miner.bloc.addTransation(message[1])
        self.addTransactionToBlock(message)
        for id, neighbor in self.miner.miners.items():
            if sender != (neighbor.host, neighbor.port):
                self.miner.sock.sendto(
                    self.miner.serialize(message),
                    (neighbor.host, neighbor.port),
                )

    def addTransactionToBlock(self, transaction):
        """Add transactions to blocks

        Parameter
        ----------
        transaction : Transaction object
        """
        print("Compute block ", len(self.miner.blockchain))
        if self.miner.blockchain == []:
            genesis = Block(-1, -1)
            genesis.closeBlock()
            self.miner.blockchain.append(
                Block(genesis.getPrevBlockHash(), genesis.getBlockNumber() + 1)
            )
        if self.miner.blockchain[-1].addTransaction(transaction):
            return

        else:
            if self.miner.blockchain[-1].getBlockHash != None:
                self.miner.blockchain[-1].closeBlock()
                self.sendBlock(self.miner.blockchain[-1])
            self.miner.blockchain.append(
                Block(
                    self.miner.blockchain[-1].getBlockHash(),
                    self.miner.blockchain[-1].getBlockNumber() + 1,
                )
            )
            self.miner.blockchain[-1].addTransaction(transaction)

    def sendBlock(self, block):
        for id, neighbor in self.miner.miners.items():
            self.miner.sock.sendto(
                self.miner.serialize(block),
                (neighbor.host, neighbor.port),
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
                print("Miners: ", self.miner.miners)
                print("\n")
                print("Wallets: ", self.miner.wallets)

            # deconnexion
            elif action == "s":
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
            # I say bye to my neighbors
            deconnectionMessage = ("bye!", self.miner.node.id)

            for id, neighbor in self.miner.miners.items():
                self.miner.sock.sendto(
                    self.miner.serialize(deconnectionMessage),
                    (neighbor.host, neighbor.port),
                )

            for id, neighbor in self.miner.wallets.items():
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
        self.miners = {}
        self.wallets = {}
        self.blockchain = []

    def run(self):
        L = Listen(self)
        A = Actions(self)
        L.start()
        A.start()

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
