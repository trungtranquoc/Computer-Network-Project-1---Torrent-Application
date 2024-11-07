import socket
from typing import Tuple, List, Union
import json


class Connection:
    """
    Client-tracker connection
    """
    __addr: Tuple[str, int]
    __conn: socket.socket             # Client-tracker socket
    __swarms_info: dict

    def __init__(self, server_addr: Tuple[str, int]):
        self.__addr = server_addr
        self.__rcv_command = None
        self.__conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        try:
            self.__conn.connect(self.__addr)

            print(f"Connect to server {self.__addr} successfully !")
        except Exception as e:
            print(f"Can not connect to server {self.__addr} due to error: {e}")

    def quit(self):
        self.__conn.close()
        print(f"Disconnect from server {self.__addr}")

    def update_swarm(self, swarms: str, pieces: int, progress: int):
        bit_flag = "".join(["1" if idx > progress else "0" for idx in range(pieces)])

        self.__swarms_info[swarms] = bit_flag

    def show_swarms(self):
        """
        Show list of swarms that the client joins
        :return:
        """
        print(f"Server: {self.__addr}")

        for idx, swarms_info in enumerate(self.__swarms_info.items()):
            swarm, bit_flag = swarms_info

            print(f"[{idx}] Key: {swarm}\n    Value: {bit_flag}")

    def get_list_of_pieces(self, key: str) -> str:
        """
        :param key: hash value of torrent of the swarm
        :return: bits-string indicating which pieces the client already has in key
        """
        return self.__swarms_info[key]


    def upload_command(self, torrent_data: str, listen_addr: Tuple[str, int]):
        ip, listen_port = listen_addr
        self.__conn.sendall(f"upload::{ip}::{listen_port}::{torrent_data}".encode())

    def download_command(self, torrent_data: str) -> Union[List[Tuple[str, int]], None]:
        """

        :param torrent_data: torrent data including metadata of downloading file.
        :return: list of address of seeders.
        """
        self.__conn.sendall(f"download::{torrent_data}".encode())

        # Receive notification message
        rcv_data = self.__conn.recv(1024).decode()
        if rcv_data is "Error":
            return None

        seeders: List[Tuple[str, int]] = json.loads(rcv_data)

        return seeders