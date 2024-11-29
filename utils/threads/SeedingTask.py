import socket
import json
import threading
from threading import Thread, Lock
from typing import List, Tuple, Union, Dict
from pathlib import Path
import sys
from custom import HostAddress, MAXSIZE_TORRENT


class ClientListenThread(Thread):
    """
    Thread for listening to download request.
    """
    __folder_path: Path
    __seed_addr: HostAddress
    __listening_socket: socket.socket
    __seeding_socket: List[socket.socket]
    __input_str: str
    __command_line_lock: Lock

    def __init__(self, folder_path: Path, addr: HostAddress, client_name: str,
                 command_line_lock: Lock, daemon: bool = True):
        """
        
        :param folder_path: folder of the client
        :param addr: listennig
        :param client_name: 
        :param daemon: 
        """
        super().__init__(daemon=daemon)
        self.__folder_path = folder_path
        self.__seed_addr = addr
        self.__listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__seeding_socket = []
        self.__input_str = client_name
        self.__command_line_lock = command_line_lock

    def print_message(self, message: str):
        """
        Print and restore the input string "client_port" into new line
        :param message: string to print
        """
        with self.__command_line_lock:
            sys.stdout.write("\033[2K\r")  # Clear the current line
            print(message)  # Print the received message on a new line
            sys.stdout.write(f"{self.__input_str}> ")  # Restore the prompt
            sys.stdout.flush()


    def run(self):
        with self.__listening_socket as listen_socket:
            listen_socket.bind(self.__seed_addr)
            listen_socket.listen(5)
            self.print_message(f'Starting listening at {self.__seed_addr} !')
            while True:
                leech_conn, leech_addr = listen_socket.accept()
                self.print_message(f'Connection with client {leech_addr} established')
                torrent_dump: str = leech_conn.recv(MAXSIZE_TORRENT).decode()
                torrent_dict: Dict = json.loads(torrent_dump)

                self.__seeding_socket.append(leech_conn)
                seeding_thread = SeedingThread(self.__folder_path,
                                               # leecher=leech_addr,
                                               torrent_data=torrent_dict,
                                               leech_conn=leech_conn)
                seeding_thread.daemon = True
                seeding_thread.start()


class SeedingThread(Thread):
    def __init__(self, folder_path: Path, torrent_data: dict, leech_conn: socket.socket):
        super().__init__()
        # self.__leech_addr: HostAddress = leecher
        self.__folder_path: Path = folder_path
        self.__file_name: str = torrent_data['name'] + torrent_data['extension']
        self.__file_size: int = torrent_data['size']
        self.__piece_size: int = torrent_data['piece_size']
        self.__socket: socket.socket = leech_conn

        try:
            with open(folder_path / self.__file_name, 'rb') as f:
                self.__data = f.read()
        except FileNotFoundError:
            print(f'Can not open file with path {folder_path / self.__file_name}')
            self.__socket.sendall('Failed'.encode())
            return

        self.__socket.sendall('OK'.encode())

    def run(self):
        with self.__socket as s:
            while True:
                data: str = s.recv(4096).decode()
                if data == "STOP":
                    break

                piece_idx: int = int(data)
                # s.sendall(send)
                s.sendall(self.__data[piece_idx * self.__piece_size : (piece_idx + 1) * self.__piece_size])


