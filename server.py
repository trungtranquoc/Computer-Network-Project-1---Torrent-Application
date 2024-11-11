import json
import socket
import threading
from typing import Tuple, Dict, Union, List
import sys
from utils import hash_torrent
import pprint
from custom import Address
from custom import server_help

HOST = "localhost"
PORT = 1232


class Server:
    __addr: Address
    __connections: Dict[Address, socket.socket]
    __listener_thread: threading.Thread
    __command_line_thread: threading.Thread
    __swarms: dict
    __swarms_lock: threading.Lock

    def __init__(self):
        self.__addr = (HOST, PORT)
        self.__listener_thread = threading.Thread(target=self._listening_for_connections, daemon=True)
        self.__command_line_thread = threading.Thread(target=self._command_line_program)

        self.__connections = {}

        self.__swarms = {}
        self.__swarms_lock = threading.Lock()

    def run(self):
        self.__listener_thread.start()
        self.__command_line_thread.start()

        # Only command line thread due to control stop of the program
        self.__command_line_thread.join()

    def add_new_swarm(self, torrent_data: dict, client_addr: Address) -> int:
        """

        :param torrent_data: json file of torrent data
        :param client_addr: (host, port) info of client
        :return: key of swarm in the list
        """
        key = hash_torrent(torrent_data)
        msg = None
        if key not in self.__swarms.keys():  # Swarm not exists yet
            with self.__swarms_lock:
                self.__swarms[key] = torrent_data
                self.__swarms[key]["seeders"] = []
                self.__swarms[key]["seeders"].append(client_addr)

            print(f"[SUCCESSFULLY] New swarm has been created: {key}")
        else:  # Swarm already exist
            if client_addr not in self.__swarms[key]["seeders"]:
                with self.__swarms_lock:
                    self.__swarms[key]["seeders"].append(client_addr)
                print(f"[SUCCESSFULLY] Add seeder to swarm {key}")
            else:
                print(f"[ERROR] Seeder already in swarm {key}")

        return key

    def get_swarm(self, key: int) -> Union[List[Address], None]:
        """

        :param torrent_data: Dictionary of torrent data
        :return: none of swarm do not exist, otherwise: none
        """
        with self.__swarms_lock:
            if key not in self.__swarms.keys():
                return None
            else:
                return self.__swarms[key]["seeders"]  # Return list of seeders

    def show_swarm(self):
        print("-" * 33)
        with self.__swarms_lock:
            if len(self.__swarms) == 0:
                print("No swarms")
            for idx, swarm_data in enumerate(self.__swarms.items()):
                key, swarm = swarm_data
                print(f"[{idx + 1}] Key: {key}")
                pprint.pprint(swarm)

                if idx < len(self.__swarms) - 1:
                    print("-" * 22)

        print("-" * 33)

    def _listening_for_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(self.__addr)
            server_socket.listen()

            print(f"[LISTENING] Server is listening on {self.__addr}")
            while True:
                client_socket, addr = server_socket.accept()

                # Save in the connections list
                client_ip, client_port = addr
                addr = client_ip, int(client_port)
                self.__connections[addr] = client_socket

                print(f"[ACCEPTED] Accepted connection from {addr}")

                connect_thread = threading.Thread(target=self._connection, args=(client_socket, addr), daemon=True)
                connect_thread.start()

    def _connection(self, conn: socket.socket, client_addr: Address):
        client_name = f"{client_addr[0]}:{client_addr[1]}"

        while True:
            command = conn.recv(4096).decode()  # Receive command here
            if not command:
                break

            info = command.split("::")
            print("-" * 33)
            print(f"{client_name}> data: {info}")

            if len(info) == 4 and info[0] == "upload":
                ip, port = info[1], info[2]
                client_addr = (ip, int(port))

                torrent_data = json.loads(info[3])
                try:
                    key = self.add_new_swarm(torrent_data, client_addr)
                    # Send key of client back to the client
                    conn.sendall(str(key).encode())
                except Exception as e:
                    print(f"[Error] Error when create swarm: {e}")

            elif len(info) == 2 and info[0] == "download":
                torrent_data = json.loads(info[1])
                key = hash_torrent(torrent_data)
                swarm_lists = self.get_swarm(key)

                if swarm_lists is None:
                    conn.sendall("Error".encode())
                else:
                    conn.sendall(f"{key}::{json.dumps(swarm_lists)}".encode())
            elif len(info) == 3 and info[0] == "download" and info[1] == "key":
                key = int(json.loads(info[2]))

                if key not in self.__swarms.keys():
                    conn.sendall("Error".encode())
                else:
                    conn.sendall(json.dumps(self.__swarms[key]).encode())
            else:
                print("[ERROR] Unknown command")

            print("-" * 33)

        print(f"Client {client_name} disconnected !")
        conn.close()

    def _command_line_program(self):
        while True:
            command = input(f"")
            info = command.split()

            if len(info) == 1 and info[0] == "quit":
                break
            elif len(info) == 1 and info[0] == "help":
                server_help()
            if len(info) == 2 and info[0] == "show" and info[1] == "swarm":
                self.show_swarm()
            else:
                print("[ERROR] Command not found")

        print("Program has been terminated!")


if __name__ == "__main__":
    server = Server()
    server.run()

    sys.exit()
