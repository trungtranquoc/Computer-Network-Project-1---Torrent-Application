import threading
import socket
from abc import ABC
from typing import Tuple

class ConnectingListeningThread(threading.Thread, ABC):
    __host_name: str
    __addr: Tuple[str, int]
    __socket: socket.socket

    def __init__(self, host_name: str, addr: Tuple[str, int]):
        super().__init__()
        __host_name = host_name
        __addr = self.__addr

    def run(self):
        # Socket listening
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(self.__addr)
        self.__socket.listen()
        print(f"[LISTENING] {self.__host_name} is listening on {self.__addr}")

        while True:
            connSocket, addr = self.__socket.accept()
            # Create a thread to handle this connection socket