import socket
from typing import Tuple, List, Union
import json
from custom import SwarmException, HostAddress, MAXSIZE_TORRENT, ServerConnectionError


class Connection:
    """
    Client-tracker connection
    """
    __addr: HostAddress
    __conn: socket.socket             # Client-tracker socket
    __swarms_info: dict
    __listen_addr: HostAddress

    def __init__(self, server_addr: HostAddress, listen_addr: HostAddress):
        self.__addr = server_addr
        self.__conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__swarms_info = {}
        self.__listen_addr = listen_addr

    def run(self):
        self.__conn.connect(self.__addr)
        print(f"Connect to server {self.__addr} successfully !")

        self.__conn.sendall(f"{self.__listen_addr[0]}::{self.__listen_addr[1]}".encode())
        server_verify_message = self.__conn.recv(1024).decode()

        if server_verify_message != 'OK':
            raise ServerConnectionError("Connection failed !")

    def show_swarms(self):
        """
        Show list of swarms that the client joins
        :return:
        """
        print(f"Server: {self.__addr}")

        for idx, swarms_info in enumerate(self.__swarms_info.items()):
            swarm, bit_flag = swarms_info

            print(f"[{idx}] Key: {swarm}\n    Value: {bit_flag}")

    def upload_command(self, torrent_data: str) -> int:
        self.__conn.sendall(f"upload::{torrent_data}".encode())
        swarm_key = self.__conn.recv(1024).decode()          # Receive key

        return int(swarm_key)

    def download_command(self, torrent_data: str) -> Tuple[int, List[HostAddress]]:
        """

        :param torrent_data (str): dump value of torrent data dictionary
        :return: key of swarm and list of seeders
        """
        self.__conn.sendall(f"download::{torrent_data}".encode())

        # Receive notification message
        rcv_data = self.__conn.recv(4096).decode()
        if rcv_data == "Error":
            raise SwarmException("Not found swarm in server")

        key, seeders_list = rcv_data.split("::")
        seeders: List[HostAddress] = [tuple(s) for s in json.loads(seeders_list)]

        if len(seeders) == 0:
            raise SwarmException("No peer in swarm")

        return int(key), seeders

    def download_magnet_link_command(self, swarm_key: str) -> Tuple[dict, List[HostAddress]]:
        """

        :param swarm_key: key of the interested swarm
        :return: torrent data and list of seeders
        """
        self.__conn.sendall(f"download::key::{swarm_key}".encode())

        # Receive notification message
        rcv_data = self.__conn.recv(MAXSIZE_TORRENT).decode()

        if rcv_data == "Error":
            raise SwarmException("Not found swarm in server")

        swarm_info: dict = json.loads(rcv_data)
        seeders: List[HostAddress] = [tuple(s) for s in swarm_info["seeders"]]
        del swarm_info["seeders"]

        if len(seeders) == 0:
            raise SwarmException("No peer in swarm")

        return swarm_info, seeders

    def get_swarms(self) -> List[dict]:
        """

        :return: List of swarm in this connected server. The data for each swarm including:
        """
        self.__conn.sendall("get_swarms".encode())
        rcv_data = self.__conn.recv(MAXSIZE_TORRENT).decode()

        if rcv_data == "Error":
            return []

        return [data | {"tracker": self.__addr} for data in json.loads(rcv_data)]

    def get_hostAddress(self) -> HostAddress:
        return self.__addr

    def quit(self):
        self.__conn.close()
        print(f"Disconnect from server {self.__addr}")