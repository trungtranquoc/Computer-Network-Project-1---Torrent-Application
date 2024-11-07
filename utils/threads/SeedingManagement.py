import socket
from threading import Thread
from typing import List, Tuple

class SeedingThread(Thread):
    __seeding_list: List[socket.socket, str]
    __addr: Tuple[str, int]

    def __init__(self, addr: Tuple[str, int]):
        __seeding_list = []
        __addr = addr

    def run(self):
        pass
