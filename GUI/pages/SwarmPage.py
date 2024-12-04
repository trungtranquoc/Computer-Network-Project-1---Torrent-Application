from tkinter import *
from typing import Tuple
from custom import HostAddress

from client import Client
from utils.Swarm import Swarm


class SwarmPage(Frame):
    def __init__(self, parent, controller, client: Client):
        super().__init__(parent, padx=10, pady=20)
        self.controller = controller
        self.client = client

        page_name = Label(self, text="Local swarm page", font=("Arial", 18), fg="#0388B4")
        page_name.grid_columnconfigure(0, weight=1)
        page_name.grid_rowconfigure(0, weight=1)
        page_name.grid(row=0, column=0, columnspan=6, sticky="ew")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        # Button
        Button(self, text="Update", command=self.update, bg="white", fg="#0388B4", font=("Arial", 10)).grid(
            column=3, row=1, sticky="e", pady=2, padx=2, ipadx=20
        )

        # Header for table
        header = Frame(self, bg="#0388B4")
        header.grid(row=2, column=0, columnspan=6, sticky="ew")

        header.grid_columnconfigure(0, minsize=30)
        header.grid_columnconfigure(1, weight=1, minsize=150)
        header.grid_columnconfigure(2, minsize=200)
        header.grid_columnconfigure(3, minsize=200)
        header.grid_columnconfigure(4, minsize=100)

        Label(header, text="No.", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=0, sticky="ew")
        Label(header, text="File name", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=1, sticky="w")
        Label(header, text="Server Address", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=2, sticky="w")
        Label(header, text="Key", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=3, sticky="w")
        Label(header, text="Status", font=('Arial', 10), fg="white", bg="#0388B4").grid(row=0, column=4, sticky="w")

        self.swarm_frames = []

    def update(self):
        # destroy old frame
        for swarm_frame in self.swarm_frames:
            swarm_frame.destroy()

        # Get swarms information
        swarms = self.client.show_swarms()
        swarm_frames = [ClientSwarmFrame(self, swarm, idx) for idx, swarm in enumerate(swarms)]

        for idx, swarm_frame in enumerate(swarm_frames):
            swarm_frame.grid(row=idx+3, column=0, columnspan=4, sticky="ew", pady=3)

class ClientSwarmFrame(Frame):
    def __init__(self, parent, swarm: Swarm, idx: int):
        super().__init__(parent, pady=2, bg="white")
        self.parent = parent
        self.file_name = swarm.file_name
        self.server_addr = swarm.server_conn.get_hostAddress()
        self.key = swarm.file_id
        self.status = swarm.get_status()
        self.idx = idx

        self.grid_columnconfigure(0, minsize=30)
        self.grid_columnconfigure(1, weight=1, minsize=150)
        self.grid_columnconfigure(2, minsize=200)
        self.grid_columnconfigure(3, minsize=200)
        self.grid_columnconfigure(4, minsize=100)

        Label(self, text=self.idx, font=("Arial", 8), bg="white", fg="black").grid(column=0, row=0, sticky="ew")
        Label(self, text=self.file_name, font=("Arial", 8), bg="white", fg="black").grid(column=1, row=0, sticky="w")
        Label(self, text=str(self.server_addr), font=("Arial", 8), bg="white", fg="black").grid(column=2, row=0, sticky="w")
        Label(self, text=self.key, font=("Arial", 8), bg="white", fg="black").grid(column=3, row=0, sticky="w")
        Label(self, text=self.status, font=("Arial", 8), bg="white", fg="black").grid(column=4, row=0, sticky="w")

        Canvas(self, height=2, bg="#0388B4", bd=0, highlightthickness=0).grid(row=1, column=0, columnspan=7,
                                                                            sticky="ew")