import socket
from sys import flags
from threading import Thread
from typing import List, Tuple, Union
from pathlib import Path

class SeedingListenThread(Thread):
    """
    Thread for listening to download request.
    """
    __port: int
    __ip_addr: str
    __listening_socket: socket.socket

    def __init__(self, port: int, ip_addr: str = "localhost"):
        pass


class SeedingThread(Thread):
    __data: bytes
    __socket: socket.socket
    __leech_addr: Tuple[str, int]


    def __init__(self, folder_path: Path, leecher: Tuple[str, int], torrent_data: dict, seed_socket: socket.socket):
        self.__leech_addr: Tuple[str, int] = leecher
        self.__folder_path: Path = folder_path
        self.__file_name: str = torrent_data['file_name']
        self.__file_size: int = torrent_data['file_size']
        self.__piece_size: int = torrent_data['piece_size']
        self.__socket: socket.socket = seed_socket

        try:
            with open(folder_path / self.__file_name, 'rb') as f:
                self.__data = f.read()
        except FileNotFoundError:
            print(f'Can not open file with path {folder_path / self.__file_name}')
            return

        self.__socket.sendall(f'ready to share file'.encode())

    def run(self):
        with self.__socket as s:
            while True:
                piece_idx: int = int(s.recv(4096).decode())
                s.sendall(self.__data[piece_idx * self.__piece_size : (piece_idx + 1) * self.__piece_size])
        pass

