from Transaction import Transaction
from random import randint
from Node import Node
import socket, sys
import pickle as pickle
import threading
import time
import uuid
import re


class Listen(threading.Thread):
    def __init__(self, wallet):
        threading.Thread.__init__(self)
        self.wallet = wallet
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

        while self.wallet.node.run:
            try:
                """
                possible messages:
                case 1 => data = Node : new neighbor
                case 2 => data = "bye!" : deconnection message
                case 3 => data = (str, UUID) : it is an ACK
                """
                try:
                    # wait for new message
                    data, sender = self.wallet.sock.recvfrom(1024)
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
        self.wallet.sock.close()  # close the link

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

            deserializedData = self.wallet.deserialize(data)
            # Is it a Node?
            if isinstance(deserializedData, Node):
                if deserializedData.type == "MINER":
                    self.processMiner(deserializedData, sender)
                elif deserializedData.type == "WALLET":
                    return

            # Is it a response?
            elif (
                isinstance(deserializedData, tuple)
                and isinstance(deserializedData[0], str)
                and isinstance(deserializedData[1], uuid.UUID)
            ):
                if deserializedData[0] == "bye!":
                    # If I know the sender I delete it
                    if deserializedData[1] in self.wallet.miners:
                        del self.wallet.miners[deserializedData[1]]

                else:
                    pass
            print("reveiced {} from {}".format(deserializedData, sender))

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
        return address == (self.wallet.node.host, self.wallet.node.port)

    def processMiner(self, miner, sender):
        """Process Miner information

        Parameter
        ----------
        miner : Node object
        sender: tuple
        """
        # new neighbor ?
        if miner.id not in self.wallet.miners:
            # I add my new neighbor to my neighbor list
            self.wallet.miners[miner.id] = miner
            # send an "ACK" => self.wallet.node
            self.wallet.sock.sendto(
                self.wallet.serialize(self.wallet.node),
                sender,
            )


class AutoSend(threading.Thread):
    __SLEEP = 3

    def __init__(self, wallet):
        threading.Thread.__init__(self)
        self.wallet = wallet

    def run(self):
        if len(self.wallet.miners) > 0:
            while self.wallet.node.run:

                time.sleep(self.__SLEEP)
                try:
                    # Send random transaction
                    for id, miner in self.wallet.miners.items():
                        transaction = Transaction(
                            str(randint(0, 100000)),
                            str(randint(0, 100000)),
                            str(randint(0, 100000)),
                        )
                        message = transaction

                        self.wallet.sock.sendto(
                            self.wallet.serialize(message), (miner.host, miner.port)
                        )
                except socket.error as e:
                    print(e, "\n message not send.")
                    pass
        else:
            print("Please try to connect to a miner")


class Actions(threading.Thread):
    def __init__(self, wallet):
        threading.Thread.__init__(self)
        self.wallet = wallet

    def run(self):
        """
        Listen keyboard
        """
        while self.wallet.node.run:

            action = input(">")

            # neighbors
            if action == "v":
                print(self.wallet.miners)

            # deconnexion
            elif action == "s":
                self.deconnection()

            elif action == "id":
                print(
                    "Host = ",
                    self.wallet.node.host,
                    "\n",
                    "Port = ",
                    self.wallet.node.port,
                    "\n",
                    "Id = ",
                    self.wallet.node.id,
                    "\n",
                    "Type = ",
                    self.wallet.node.type,
                )

            elif action == "test":
                pass

            elif action == "connect":
                self.connection()

            elif action == "send":
                self.sendMessage()

            elif action == "auto send":
                # self.autoSendMessage()
                if len(self.wallet.miners) > 0:
                    self.autoSendMessage()

                else:
                    print("Please try to connect to a miner")
                    self.connection()
                    self.autoSendMessage()
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
            self.wallet.sock.sendto(
                self.wallet.serialize(self.wallet.node),
                address,
            )
        except socket.error as e:
            print(e, "\nconnection failed.")
            pass

    def deconnection(self):
        """
        Stop the socket, the thread and send deconnection message to neighbors
        """
        try:
            for id, miner in self.wallet.miners.items():
                # I say bye to my neighbors
                deconnectionMessage = ("bye!", self.wallet.node.id)

                self.wallet.sock.sendto(
                    self.wallet.serialize(deconnectionMessage),
                    (miner.host, miner.port),
                )

            self.wallet.node.run = False  # stop runnig
            print("Close")

        except Exception as e:
            print(e, "\n deconnection failed.")
            sys.exit()

    def sendMessage(self):
        """
        Send message
        """
        if len(self.wallet.miners) > 0:
            # Ask the message to send
            message = (input("Please enter your message:"), self.wallet.node.id)
            try:
                # Send the message
                for id, miner in self.wallet.miners.items():
                    self.wallet.sock.sendto(
                        self.wallet.serialize(message), (miner.host, miner.port)
                    )
            except socket.error as e:
                print(e, "\n message not send.")
                pass

        else:
            print("Please try to connect to a miner")
            self.connection()
            # self.sendMessage()

    def autoSendMessage(self):
        """
        Send message automaticaly
        """
        A = AutoSend(self.wallet)
        A.start()


class Wallet:
    __type = "WALLET"
    __timeout = 0.0000001

    def __init__(self, host=socket.gethostname(), port=1234):
        self.node = Node(host, port, self.__type)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.settimeout(self.__timeout)
        self.sock.bind((self.node.host, self.node.port))
        self.miners = {}

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


Wallet = Wallet(sys.argv[1], sys.argv[2])
Wallet.run()
