import os
import json
import socket
import sys
from pathlib import Path
from threading import Thread
from typing import Dict, Union, List, Tuple
import threading
from utils import Connection, generate_torrent_file
from utils.Swarm import Swarm, SeederSwarm, SwarmStatus
from utils.threads import DownloadThread, ClientListenThread
from custom import (HostAddress, ServerConnectionError, DownloadFileException,
                    DEFAULT_PIECE_SIZE)
from custom import client_help


class Client(Thread):
    __client_addr: HostAddress
    __listen_addr: HostAddress
    __connections: Dict[HostAddress, Connection]
    __folder_path: Union[str, Path]
    __listener_thread: ClientListenThread
    __swarms: Dict[int, Swarm]
    __download_tasks: Dict[int, DownloadThread]

    command_line_lock = threading.Lock()

    def __init__(self, port: int, listen_port: int, ip: str = "localhost"):
        super().__init__()
        self.__client_addr = (ip, port)
        self.__listen_addr = (ip, listen_port)
        self.__folder_path = Path(os.getcwd()) / f'client_{port}'
        self.__connections = {}
        self.__swarms = {}
        self.__download_tasks = {}

        self.__listener_thread = ClientListenThread(self.__folder_path, addr=self.__listen_addr,
                                                    client_name=f"client_{port}",
                                                    command_line_lock=self.command_line_lock)

        # Case client not exist yet, then we add directory
        if not os.path.exists(self.__folder_path):
            os.makedirs(self.__folder_path)
        torrent_folder = Path(self.__folder_path) / 'torrents'
        if not os.path.exists(torrent_folder):
            os.makedirs(torrent_folder)

    def run(self):
        self.__listener_thread.start()  # Start listener thread

    def get_ip_addr(self):
        return self.__client_addr

    def create_torrent_file(self, file_name: str,
                            server_addr: HostAddress = ("localhost", 1232),
                            piece_size: int = DEFAULT_PIECE_SIZE):
        """
        create torrent file for a sharing file

        :param file_name: name of the file
        :param server_addr: address and port of the server
        :param piece_size: size of each piece
        """
        file_path = Path(self.__folder_path) / file_name
        output_dir = self.__folder_path / 'torrents'

        print(f"Create torrent file {file_name} that connect to tracker {server_addr}...")

        try:
            torrent_path = generate_torrent_file(file_path, output_dir, server_addr, piece_size)

            print(f"[SUCCESSFULLY] New torrent file has been created in {torrent_path} !")
        except Exception as e:
            print(f"[ERROR] Can not create new torrent file due to error: {e}")

    def upload_torrent(self, torrent_file: str):
        try:
            with open(Path(self.__folder_path) / 'torrents' / torrent_file, 'r') as tf:
                data: dict = json.load(tf)

            # Get server connection
            ip, port = data['tracker'].values()  # Convert dictionary {"tracker": { "ip": ip_addr, "port": port} to (ip_addr, port)
            server_addr = (ip, int(port))
            print(f"Upload file to server {server_addr}...")
            server_conn: Connection = self.__connect_server(server_addr)

            if server_conn is None:
                raise Exception("Failed to connect to server")

            # Send data
            swarm_key = server_conn.upload_command(json.dumps(data))

            if swarm_key in self.__swarms.keys():
                raise Exception(f'Client already in this swarm ! Swarm key: {swarm_key}')

            # Save information of swarm
            file_name = data['name'] + data['extension']
            swarm_data = SeederSwarm(swarm_key, server_conn, file_name)
            self.__swarms[swarm_key] = swarm_data

            print(f'[SUCCESSFULLY] New swarm has been created in server: {swarm_key} !')

        except FileNotFoundError:
            print('[ERROR] Can not open torrent file')
        except Exception as e:
            print(f"[ERROR] Can not start upload torrent file due to error: {e}")

    def skip_progress(self, file_id: int):
        print(f"\nSkip downloading file {file_id}...")

        if file_id not in self.__download_tasks.keys():
            print('[ERROR] Can not find process')
            return

        download_task = self.__download_tasks[file_id]
        if not download_task.is_downloading():
            print('[ERROR] File is not downloading')
        else:
            download_task.skip_download()
            print(f'[SUCCESSFULLY] Skip downloading file with id {file_id}')

    def start_download(self, torrent_file: str):
        print(f"Start downloading file {torrent_file}...")

        try:
            with open(Path(self.__folder_path) / 'torrents' / torrent_file, 'r') as tf:
                data: Dict = json.load(tf)

                # Get server connection
                ip, port = data['tracker'].values()
                server_addr = (ip, int(port))
                print(f"Download file from server {server_addr}")
                server_conn: Connection = self.__connect_server(server_addr)
                if server_conn is None:
                    raise ServerConnectionError(f'Can not connect to server {server_addr}')

                # Send data
                swarm_key, seeders = server_conn.download_command(torrent_data=json.dumps(data))
                self.__download(server_conn=server_conn, torrent_data=data,
                                swarm_key=swarm_key, seeders=seeders)
        except FileNotFoundError:
            print('[ERROR] Can not open torrent file')
            return
        except Exception as e:
            print(f'[ERROR] Can not start download file due to error: {e}')
            return

    def start_magnet_link_download(self, magnet_link: str):
        ip, port, swarm_key = magnet_link.split('::')
        server_addr = (ip, int(port))

        print(f"Start downloading file {swarm_key} from server {server_addr}...")

        server_conn: Connection = self.__connect_server(server_addr)

        # Send data
        try:
            if server_conn is None:
                raise ServerConnectionError(f'Can not connect to server {server_addr}')
            torrent_data, seeders = server_conn.download_magnet_link_command(swarm_key=swarm_key)
            self.__download(server_conn=server_conn, torrent_data=torrent_data,
                            swarm_key=int(swarm_key), seeders=seeders)
        except Exception as e:
            print(f"[ERROR] Can not start download magnet link due to error: {e}")

    def show_directory(self) -> Tuple[List[str], List[str]]:
        files: List[str] = []
        torrent_files: List[str] = []

        print(f"Show directory...")

        for f in os.listdir(self.__folder_path):
            print(f'-> {f}')

            if f != "torrents":
                files.append(f)

            if os.path.isdir(self.__folder_path / f):
                for file in os.listdir(self.__folder_path / f):
                    print(f'---> {file}')
                    torrent_files.append(file)

        return files, torrent_files

    def show_progress(self) -> List[DownloadThread]:
        if len(self.__download_tasks) == 0:
            print("The client has not yet started any downloading !")
        else:
            for idx, download_task in enumerate(self.__download_tasks.values()):
                bit_field = download_task.bit_field
                progress = bit_field.count('1') / len(bit_field) * 100
                bit_string = "".join(bit_field)
                print(f"[{idx + 1}] {download_task.file_id}")
                if download_task.is_error():
                    print(
                        f"    {download_task.status} - {progress:.2f}% - {bit_string} - Error: {download_task.error_message}")
                else:
                    print(f"    {download_task.status} - {progress:.2f}% - {bit_string}")

        return list(self.__download_tasks.values())

    def show_swarms(self) -> List[Swarm]:
        """
            Retrieve list of swarms that this client is joining
        :return:
        """
        print("Show swarm...")

        if len(self.__swarms) == 0:
            print("The client has not joined any swarm !")
        else:
            for idx, swarm in enumerate(self.__swarms.values()):
                print(f"[{idx + 1}] {swarm.server_conn.get_hostAddress()} - {swarm.file_id} - {swarm.get_status()}")

        return list(self.__swarms.values())

    def get_all_swarms(self) -> List[dict]:
        """
        Return all swarms of all connected server

        :return: each swarm include data:
        - tracker: server ip address and port.
        - key: swarm key in tracked by that server.
        - name: name of the file in the swarm.
        - size: size of the file.
        - seeders: number of seeders available in that swarm.
        """
        swarm_data: List[dict] = []

        print("Load swarms information from all connected servers...")

        if not self.__connections.keys():
            print("The client has not yet connect to any server !")

        try:
            for server_conn in self.__connections.values():
                swarm_data  += server_conn.get_swarms()

            swarm_data  = [swarm | {'no': idx+1} for idx, swarm in enumerate(swarm_data)]
            for swarm in swarm_data:
                print(f"[{swarm['no']}] - {swarm['tracker']} - {swarm['key']} - {swarm['name']} - {swarm['size']} - Seeders: {swarm['seeders']}")
            return swarm_data
        except Exception as e:
            print(f"[ERROR] Can not retrieve swarms due to error: {e}")

    def get_all_servers(self) -> List[HostAddress]:
        """

        :return: All connecting servers to this peer
        """
        return [server_conn.get_hostAddress() for server_conn in self.__connections.values()]

    def connect_server(self, server_addr: HostAddress) -> Connection:
        """

        :param server_addr: Ip address of server
        :return: Connection to server
        """
        return self.__connect_server(server_addr)

    def get_download_thread(self, file_id: int) -> DownloadThread:
        """

        :param file_id: file_id of the downloading file
        :return: DownloadThread of the file
        """
        return self.__download_tasks[file_id]

    def quit(self) -> None:
        """
        Disconnect to all server and quit the program

        :return: None
        """
        for connection in self.__connections.values():
            connection.quit()

        print("Program has been terminated!")


    def __download(self, server_conn: Connection, torrent_data: dict, swarm_key: int, seeders: List[HostAddress]):
        if swarm_key in self.__swarms.keys() and self.__swarms[swarm_key].get_status() == SwarmStatus.SEEDER:
            raise DownloadFileException('Client is the seeder of the swarm !')

        if (swarm_key in self.__download_tasks.keys() and not
        (self.__download_tasks[swarm_key].is_error() or self.__download_tasks[swarm_key].is_skip())):
            raise DownloadFileException('Client have already download or is downloading !')

        download_task = DownloadThread(file_id=swarm_key, torrent_data=torrent_data, seeders=seeders,
                                       server_conn=server_conn, download_dir=self.__folder_path,
                                       listen_addr=self.__listen_addr)
        # Save information into swarm
        self.__download_tasks[swarm_key] = download_task
        self.__swarms[swarm_key] = download_task

        print(f'Download file with id {swarm_key} ! Seeders list: {seeders}')

        download_task.start()

    def __connect_server(self, server_addr: HostAddress):
        if server_addr not in self.__connections.keys():
            try:
                self.__connections[server_addr] = Connection(server_addr, self.__listen_addr)
                self.__connections[server_addr].run()
            except Exception as e:
                print(f"Can not connect to server {server_addr} due to error: {e}")
                if server_addr in self.__connections.keys():
                    del self.__connections[server_addr]

                return None

        return self.__connections[server_addr]

def command_line_program(client: Client):
    while True:
        command = input(f"\nclient_{client.get_ip_addr()[1]}> ")

        if command == "quit":
            break

        info = command.split()
        with client.command_line_lock:
            print("-" * 33)

            if len(info) == 5 and info[0] == "create" and info[1] == "torrent":
                server_addr = info[3], int(info[4])
                client.create_torrent_file(file_name=info[2], server_addr=server_addr)
            elif len(info) == 6 and info[0] == "create" and info[1] == "torrent":
                server_addr = info[3], int(info[4])
                piece_size = int(info[5])
                client.create_torrent_file(file_name=info[2], server_addr=server_addr, piece_size=piece_size)
            elif len(info) == 2 and info[0] == "upload":
                client.upload_torrent(torrent_file=info[1])
            elif len(info) == 2 and info[0] == "download":
                client.start_download(torrent_file=info[1])
            elif len(info) == 3 and info[0] == "download" and info[1] == "key":
                client.start_magnet_link_download(magnet_link=info[2])
            elif len(info) == 2 and info[0] == "skip":
                client.skip_progress(int(info[1]))
            elif len(info) == 2 and info[0] == "show" and info[1] == "progress":
                client.show_progress()
            elif len(info) == 2 and info[0] == "show" and info[1] == "directory":
                client.show_directory()
            elif len(info) == 2 and info[0] == "show" and info[1] == "swarm":
                client.show_swarms()
            elif len(info) == 3 and info[0] == "show" and info[1] == "server" and info[2] == "swarm":
                client.get_all_swarms()
            elif len(info) == 1 and info[0] == "help":
                client_help()
            elif len(info) == 0:
                pass
            else:
                print("[ERROR] Command not found")

            print("-" * 33)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Please provide a port number for command line program and listening port !')
        sys.exit(1)

    # Read port number
    ip_addr = socket.gethostbyname(socket.gethostname())
    port = int(sys.argv[1])

    # Start client program
    listen_port = int(sys.argv[2])
    client = Client(port, listen_port, ip_addr)
    client.start()

    # Start command_line_program
    command_line_program(client)

    # Delete all connections to server
    client.quit()

    sys.exit()
