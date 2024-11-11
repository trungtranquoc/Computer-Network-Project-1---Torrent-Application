import socket
from typing import Tuple, List, Union
import json
from custom import SwarmException, HostAddress

class Connection:
    """
    Client-tracker connection
    """
    __addr: HostAddress
    __conn: socket.socket             # Client-tracker socket
    __swarms_info: dict

    def __init__(self, server_addr: HostAddress):
        self.__addr = server_addr
        self.__rcv_command = None
        self.__conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__swarms_info = {}

    def run(self):
        try:
            self.__conn.connect(self.__addr)

            print(f"Connect to server {self.__addr} successfully !")
        except Exception as e:
            raise Exception(e)

    def show_swarms(self):
        """
        Show list of swarms that the client joins
        :return:
        """
        print(f"Server: {self.__addr}")

        for idx, swarms_info in enumerate(self.__swarms_info.items()):
            swarm, bit_flag = swarms_info

            print(f"[{idx}] Key: {swarm}\n    Value: {bit_flag}")

    def upload_command(self, torrent_data: str, listen_addr: HostAddress) -> int:
        ip, listen_port = listen_addr
        self.__conn.sendall(f"upload::{ip}::{listen_port}::{torrent_data}".encode())
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
        rcv_data = self.__conn.recv(4096).decode()
        if rcv_data == "Error":
            raise SwarmException("Not found swarm in server")

        swarm_info: dict = json.loads(rcv_data)
        seeders: List[HostAddress] = [tuple(s) for s in swarm_info["seeders"]]
        del swarm_info["seeders"]

        if len(seeders) == 0:
            raise SwarmException("No peer in swarm")

        return swarm_info, seeders

    def get_hostAddress(self):
        return self.__addr

    def quit(self):
        self.__conn.close()
        print(f"Disconnect from server {self.__addr}")