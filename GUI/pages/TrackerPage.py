from tkinter import *
from typing import Tuple
from custom import HostAddress

from client import Client

class NetworkPage(Frame):
    def __init__(self, parent, controller, client: Client):
        super().__init__(parent, padx=10, pady=20)
        self.controller = controller
        self.client = client

        page_name = Label(self, text="Server swarm page", font=("Arial", 18), fg="#0388B4")
        page_name.grid_columnconfigure(0, weight=1)
        page_name.grid_rowconfigure(0, weight=1)
        page_name.grid(row=0, column=0, columnspan=6, sticky="ew")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)
        self.grid_columnconfigure(5, weight=1)

        # Button
        self.update_button = Button(self, text="Update", command=self.update,
                                    bg="white", fg="#0388B4", font=("Arial", 10))
        self.connect_button = Button(self, text="Connect server", command=self.__connect_server,
                                    bg="white", fg="#0388B4", font=("Arial", 10))
        self.update_button.grid(column=4, row=1, columnspan=2, sticky="ew", pady=2, padx=2)
        self.connect_button.grid(column=2, row=1, columnspan=2, sticky="ew", pady=2, padx=2)

        # Header for table
        header = Frame(self, bg="#0388B4")
        header.grid(row=2, column=0, columnspan=7, sticky="ew")

        header.grid_columnconfigure(0, minsize=30)
        header.grid_columnconfigure(1, minsize=200)
        header.grid_columnconfigure(2, minsize=150)
        header.grid_columnconfigure(3, minsize=150)
        header.grid_columnconfigure(4, minsize=50)
        header.grid_columnconfigure(5, minsize=20)
        header.grid_columnconfigure(6, minsize=100)

        Label(header, text="No.", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=0, sticky="ew")
        Label(header, text="Name", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=1, sticky="w")
        Label(header, text="Server Address", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=2, sticky="w")
        Label(header, text="Key", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=3, sticky="w")
        Label(header, text="Size", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=4, sticky="w")
        Label(header, text="Seeders", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=5, sticky="w")

        self.swarm_frames = []

    def update(self):
        # destroy old frame
        for swarm_frame in self.swarm_frames:
            swarm_frame.destroy()

        # Get swarms information
        swarms = self.client.get_all_swarms()
        swarm_frames = [SwarmFrame(self, swarm) for swarm in swarms]

        for idx, swarm_frame in enumerate(swarm_frames):
            swarm_frame.grid(row=idx+3, column=0, columnspan=7, sticky="ew")

    def __connect_server(self):
        ConnectServerWindow(self)

class SwarmFrame(Frame):
    def __init__(self, parent, swarm: dict):
        super().__init__(parent, pady=2, bg="white")
        self.parent = parent
        self.no = swarm['no']
        self.name = swarm['name']
        self.tracker = swarm['tracker']
        self.key = swarm['key']
        self.size = swarm['size']
        self.seeders = swarm['seeders']

        self.grid_columnconfigure(0, minsize=30)
        self.grid_columnconfigure(1, minsize=200)
        self.grid_columnconfigure(2, minsize=150)
        self.grid_columnconfigure(3, minsize=150)
        self.grid_columnconfigure(4, minsize=50)
        self.grid_columnconfigure(5, minsize=20)
        self.grid_columnconfigure(6, weight=1, minsize=100)

        Label(self, text=self.no, font=("Arial", 8), bg="white", fg="black").grid(column=0, row=0, sticky="ew")
        Label(self, text=self.name, font=("Arial", 8), bg="white", fg="black").grid(column=1, row=0, sticky="w")
        Label(self, text=self.tracker, font=("Arial", 8), bg="white", fg="black").grid(column=2, row=0, sticky="w")
        Label(self, text=self.key, font=("Arial", 8), bg="white", fg="black").grid(column=3, row=0, sticky="w")
        Label(self, text=self.size, font=("Arial", 8), bg="white", fg="black").grid(column=4, row=0, sticky="w")
        Label(self, text=self.seeders, font=("Arial", 8), bg="white", fg="black").grid(column=5, row=0, padx=5, sticky="ew")
        Button(self, text="Download", font=('Arial', 8), bg="#0388B4", fg="white", command=self.download).grid(column=6, row=0, sticky="e", ipadx=15)

        Canvas(self, height=2, bg="#0388B4", bd=0, highlightthickness=0).grid(row=1, column=0, columnspan=7,
                                                                            sticky="ew")
    def download(self):
        ip, port = self.tracker
        self.parent.client.start_magnet_link_download(f"{ip}::{port}::{self.key}")

class ConnectServerWindow(Toplevel):
    def __init__(self, parent):
        super().__init__(parent, padx=5, pady=5)
        self.parent = parent
        self.server_conn_frames = []
        self.server_ip = StringVar()
        self.server_port = StringVar()

        Label(self, text="Add new server", font=('Arial', 12), fg="black").grid(column=0, row=0,
                                                                                columnspan=4, sticky="w", pady=10)

        Label(self, text="Ip: ", font=('Arial', 9), fg="black").grid(column=0, row=1, sticky="w")
        Entry(self, textvariable=self.server_ip).grid(column=1, row=1, sticky="ew", padx=4, pady=5)
        Label(self, text="Port: ", font=('Arial', 9), fg="black").grid(column=2, row=1, sticky="w")
        Entry(self, textvariable=self.server_port).grid(column=3, row=1, sticky="ew", pady=5, padx=4)

        Button(self, text="Add", command=self.__connect, fg="#0388B4", bg="white").grid(column=3, row=2, ipadx=10,
                                                                                        padx=4, sticky="e")

        Label(self, text="All connected servers", font=('Arial', 12), fg="black").grid(column=0, row=3,
                                                                                columnspan=4, sticky="w", pady=4)

        self.__update()

    def __update(self):
        for server_conn_frame in self.server_conn_frames:
            server_conn_frame.destroy()

        self.server_conn_frames = [ServerFrame(self, server_addr, idx)
                                   for idx, server_addr in enumerate(self.parent.client.get_all_servers())]
        for idx, server_conn_frame in enumerate(self.server_conn_frames):
            server_conn_frame.grid(row=idx+4, column=0, columnspan=4, sticky="ew", padx=4, pady=4)

    def __connect(self):
        self.parent.client.connect_server((self.server_ip.get(), int(self.server_port.get())))
        self.parent.update()
        self.__update()


class ServerFrame(Frame):
    def __init__(self, parent, server_addr: HostAddress, idx: int):
        super().__init__(parent, padx=5, pady=2, bg="white")

        self.grid_columnconfigure(0, weight=1)
        Label(self, text=f"[{idx}]", font=('Arial', 9), bg="white").grid(column=0, row=0, sticky="w")
        Label(self, text=str(server_addr), font=('Arial', 9), bg="white").grid(column=0, row=0, sticky="w")

        Canvas(self, height=2, bg="#0388B4", bd=0, highlightthickness=0).grid(row=1, column=0, columnspan=3, sticky="ew")
