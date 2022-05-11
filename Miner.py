# -*- coding: utf-8 -*-
"""
@author: Loba
"""
import traceback
from Transaction import Transaction
from Node import Node
from Block import Block
import pickle as pickle
import socket, sys
import threading
import time
import uuid
import re
import time

# from ping3 import ping

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
            if self.miner.node.run:
                neighbors_copy = neighbors_copy = self.miner.neighbors.copy()

                if not neighbors_copy:
                    continue
                else:
                    for id, neighbor in neighbors_copy.items():
                        # I say bye to my neighbors
                        deconnectionMessage = (
                            "Ping",
                            self.miner.node.id,
                            self.miner.node.host,
                            self.miner.node.port,
                        )
                        self.miner.pinged = neighbor.id

                        self.miner.sock.sendto(
                            self.miner.serialize(deconnectionMessage),
                            (neighbor.host, neighbor.port),
                        )

                        # time.sleep(10)

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

        self.__sendBlockchainRequest = re.compile("sendMe\[[0-9]+\]")

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
                    data, sender = self.miner.sock.recvfrom(131072)
                    # ignore self sended messages
                    if not self.sendToMyself(sender):
                        self.processData(data, sender)
                    else:
                        continue
                except socket.timeout as e:
                    continue
            ### Arrive quand on envoie un message à qqn qui n'existe pas avec la classe PingActions
            except socket.error as e:
                print(self.miner.pinged, "not respond")
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

            deserializedData = self.miner.deserialize(data)
            # Is it a Node?
            if isinstance(deserializedData, Node):
                if deserializedData.type == "MINER":
                    self.processMiner(deserializedData, sender)
                elif deserializedData.type == "WALLET":
                    self.processWallet(deserializedData, sender)
            # Is it a Block?
            if isinstance(deserializedData, Block):
                self.processBlock(deserializedData, sender)
            # Is it a Transaction?
            elif isinstance(deserializedData, Transaction):
                self.broadcast(deserializedData, sender)

            # Is it a message?
            elif (
                isinstance(deserializedData, tuple)
                and isinstance(deserializedData[0], str)
                and isinstance(deserializedData[1], uuid.UUID)
            ):
                if deserializedData[0] == "bye!":
                    # If I know the sender I delete it
                    if deserializedData[1] in self.miner.neighbors:
                        del self.miner.neighbors[deserializedData[1]]
                    elif deserializedData[1] in self.miner.wallets:
                        del self.miner.wallets[deserializedData[1]]
                        
                # if deserializedData[0] == "Check Proof Please":
                #     if len(self.miner.blockchain) >= 2:
                #         self.miner.blockchain[-1].checkTransaction()

                if self.__sendBlockchainRequest.match(deserializedData[0]):
                    # self.processBlockRequest(deserializedData[0], sender)
                    request = self.cleanSendBlockRequest(deserializedData[0])
                    thread = threading.Thread(
                        target=self.processBlockRequest(request, sender),
                        args=(),
                    )
                    thread.start()
            ## Is it a message to check the merkle Tree?
            elif (
                isinstance(deserializedData, tuple)
                and isinstance(deserializedData[0], tuple)
                and isinstance(deserializedData[1], uuid.UUID)
            ):
                if deserializedData[0][0] == "Check":
                    if len(self.miner.blockchain) >= 2:
                        x = self.miner.blockchain[-1].checkTransaction(deserializedData[0][1])
                        try: 

                                print(x)
                                self.miner.sock.sendto(
                                self.miner.serialize(x),
                                sender,
                            )
                        except socket.error as e:
                            print(e, '\n message not send.')
                            pass
            
            print("reveiced {} from {}".format(deserializedData, sender))

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
            # I send it my blockchain
            self.processBlockRequest(-1, sender)
            # I add my new neighbor to my neighbor list
            self.miner.neighbors[node.id] = node
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
        for id, neighbor in self.miner.neighbors.items():
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
        print("Compute block ", len(self.miner.blockchain) - 1)

        if self.miner.myBlock.addTransaction(transaction):
            return

        else:

            self.miner.myBlock != None
            thread = threading.Thread(
                target=self.miner.myBlock.closeBlock(),
                args=(),
            )
            thread.start()
            print("Taille du block {}".format(sys.getsizeof(self.miner.myBlock)))
            self.sendBlock(self.miner.myBlock)

            self.miner.blockchain.append(self.miner.myBlock)

            self.miner.myBlock = Block(
                self.miner.blockchain[-1].getBlockHash(),
                self.miner.blockchain[-1].getBlockNumber() + 1,
            )
            self.miner.myBlock.addTransaction(transaction)

    def sendBlock(self, block, dest=None):
        if isinstance(block, Block):
            if dest is None:
                for id, neighbor in self.miner.neighbors.items():
                    self.miner.sock.sendto(
                        self.miner.serialize(block),
                        (neighbor.host, neighbor.port),
                    )

            # elif (
            #     isinstance(dest, tuple)
            #     and isinstance(dest[0], str)
            #     and isinstance(dest[1], int)
            # ):
            else:
                self.miner.sock.sendto(
                    self.miner.serialize(block),
                    dest,
                )
            # print("send block {}".format(block.getBlockNumber()))

    def processBlock(self, block, sender):
        print(
            "received block n° {}; lastBlock block {}".format(
                block.getBlockNumber(),
                self.miner.blockchain[-1].getBlockNumber(),
            )
        )

        # print(
        #     "received block prevBlockHash {}; lastBlock blockHash {}".format(
        #         block.getPrevBlockHash(),
        #         self.miner.blockchain[-1].getBlockHash(),
        #     )
        # )

        if block.getBlockNumber() >= self.miner.myBlock.getBlockNumber():
            if (
                block.getBlockNumber() > self.miner.blockchain[-1].getBlockNumber() + 1
            ):  # ==> demander le block qui suit le block juste apres mon dernier block et verifier la compatibilité
                # send me your blockchain from self.miner.blockchain[-1].getId() + 1

                request = (
                    "sendMe[{}]".format(self.miner.blockchain[-1].getBlockNumber() + 1),
                    self.miner.node.id,
                )
                self.miner.sock.sendto(self.miner.serialize(request), sender)
                print(
                    "send request for block {} => my last one is {}".format(
                        block.getBlockNumber(),
                        self.miner.blockchain[-1].getBlockNumber(),
                    )
                )

        if block.getPrevBlockHash() == self.miner.blockchain[-1].getBlockHash():
            print("add {} => to my blockchain".format(block.getBlockNumber()))
            self.miner.blockchain.append(block)
            self.miner.myBlock.setPrevBlockHash(block.getPrevBlockHash())
            self.miner.myBlock.setBlockNumber(block.getBlockNumber() + 1)

        # elif self.miner.blockchain[-1].getBlockHash() == None and block.
        else:
            pass

    def processBlockRequest(self, firstBlockId, sender):
        # blockId = self.cleanSendBlockRequest(request)
        print("synchronize ... with {}".format(sender))
        while firstBlockId < len(self.miner.blockchain):
            self.sendBlock(self.miner.blockchain[firstBlockId], sender)
            firstBlockId += 1

    def cleanSendBlockRequest(self, request):
        try:
            return int(
                re.search(
                    "[0-9]+",
                    request,
                ).group(0)
            )
        except Exception as e:
            print("Other_Regex_Error", e)
            traceback.print_exc()
            pass


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
                print("neighbors: ", self.miner.neighbors)
                print("\n")
                print("Wallets: ", self.miner.wallets)

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
            # I say bye to my neighbors
            deconnectionMessage = ("bye!", self.miner.node.id)

            for id, neighbor in self.miner.neighbors.items():
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
        self.pinged = 0
        self.neighbors = {}
        self.wallets = {}
        self.blockchain = []
        genesis = Block(-1, -1)
        genesis.closeBlock()
        self.myBlock = Block(genesis.getBlockHash(), genesis.getBlockNumber() + 1)
        self.blockchain.append(genesis)

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
