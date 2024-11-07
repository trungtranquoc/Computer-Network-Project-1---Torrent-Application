import socket
from threading import Thread
from typing import Tuple, Union


class Connection:
    __addr: Tuple[str, int]
    __socket: socket.socket             # Client-tracker socket
    __swarms_info: dict

    def __init__(self, server_addr: Tuple[str, int]):
        self.__addr = server_addr
        self.__rcv_command = None
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        try:
            self.__socket.connect(self.__addr)

            print(f"Connect to server {self.__addr} successfully !")
        except Exception as e:
            print(f"Can not connect to server {self.__addr} due to error: {e}")

    def send_command(self, command: str, data: str):
        if command == "upload":
            self._upload_command(data)
        elif command == "download":
            self._download_command(data)
        else:
            print("[ERROR] Command is not supported")

    def quit(self):
        self.__socket.close()
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


    def _upload_command(self, torrent_data: str):
        self.__socket.sendall(f"upload::{torrent_data}".encode())

    def _download_command(self, torrent_data: str):
        self.__socket.sendall(f"download::{torrent_data}".encode())