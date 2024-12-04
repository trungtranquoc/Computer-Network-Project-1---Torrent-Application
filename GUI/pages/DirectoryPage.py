from tkinter import *
from tokenize import String

from client import Client

class DirectoryPage(Frame):
    def __init__(self, parent, controller, client: Client):
        super().__init__(parent, padx=10, pady=20)
        self.controller = controller
        self.client = client

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        page_name = Label(self, text="Directory Page", font=("Arial", 18), fg="#0388B4")
        page_name.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.file_frames = []
        self.torrent_file_frames = []

        Label(self, text="Directory Path", fg="#0388B4", font=('Arial', 14, "bold")).grid(row=2, column=0, sticky="w")

        # Update button
        self.update_button = Button(self, text="Update", font=('Arial', 10), bg="#0388B4", fg="white", command=self.update)
        self.update_button.grid(row=1, column=2, sticky="ew", pady=2)

        self.update()

    def create_torrent(self, file_name: str):
        window = CreateTorrentWindow(self, file_name)

    def update(self):
        # destroy old frame
        for file_frame in self.file_frames:
            file_frame.destroy()
        for torrent_file_frame in self.torrent_file_frames:
            torrent_file_frame.destroy()

        files, torrents_file = self.client.show_directory()
        self.file_frames = [FileFrame(self, self.controller, file) for file in files]

        for idx, file_frame in enumerate(self.file_frames):
            file_frame.grid(row=idx+3, column=0, columnspan=3, sticky="ew")

        # Torrent directory
        Label(self, text="Torrents", font=("Arial", 14, "bold"), fg="#0388B4").grid(row=3+len(self.file_frames),
                                                                            column=0, sticky="w", padx=5, pady=5)

        # Torrent file frames
        self.torrent_file_frames = [TorrentFileFrame(self, self.controller, file) for file in torrents_file]

        for idx, torrent_file_frame in enumerate(self.torrent_file_frames):
            torrent_file_frame.grid(row=idx+4+len(self.file_frames), column=0, columnspan=2, sticky="ew")

class FileFrame(Frame):
    def __init__(self, parent, controller, file_name: str):
        super().__init__(parent, padx=5, pady=2, bg="white")
        self.parent = parent
        self.file_name = file_name

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=0)

        text = Label(self, text=file_name, font=("Arial", 10), bg="white")
        text.grid(column=0, row=0, columnspan=2, sticky="w", ipadx=2, ipady=2)

        button = Button(self, text="Create torrent", font=("Arial", 10), bg="white", fg="#0388B4", command=self.__create_torrent)
        button.grid(column=2, row=0, ipadx=2, ipady=2, sticky="e")

        Canvas(self, height=2, bg="#0388B4", bd=0, highlightthickness=0).grid(row=1, column=0, columnspan=3, sticky="ew")

    def __create_torrent(self):
        self.parent.create_torrent(self.file_name)

class TorrentFileFrame(Frame):
    def __init__(self, parent, controller, file_name: str):
        super().__init__(parent, padx=5, pady=2, bg="white")
        self.parent = parent
        self.file_name = file_name

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)

        text = Label(self, text=file_name, font=("Arial", 8), bg="white")
        text.grid(column=0, row=0, columnspan=2, sticky="w", ipadx=2, ipady=2)

        upload_button = Button(self, text="Upload torrent", font=("Arial", 8), bg="white", fg="#0388B4",
                               command=lambda: self.parent.client.upload_torrent(self.file_name))
        upload_button.grid(column=2, row=0, ipadx=2, ipady=1, sticky="e")

        download_button = Button(self, text="Download file", font=("Arial", 8), bg="white", fg="#0388B4",
                                 command=lambda: self.parent.client.start_download(self.file_name))
        download_button.grid(column=1, row=0, ipadx=2, padx=5, ipady=1, sticky="e")

        Canvas(self, height=2, bg="#0388B4", bd=0, highlightthickness=0).grid(row=1, column=0, columnspan=3, sticky="ew")

class CreateTorrentWindow(Toplevel):
    def __init__(self, parent, file_name: str):
        super().__init__(parent)
        self.parent = parent
        self.file_name = file_name
        self.server_ip = StringVar()
        self.server_port = StringVar()
        self.pieces_size = StringVar()

        self.title(f"Create Torrent {file_name}")

        Label(self, text="Server Ip", font=("Arial", 10), fg="black", anchor="w").grid(row=0, column=0, sticky="ew")
        Label(self, text="Server Port", font=("Arial", 10), fg="black", anchor="w").grid(row=2, column=0, sticky="ew")
        Label(self, text="Pieces Size", font=("Arial", 10), fg="black", anchor="w").grid(row=4, column=0, sticky="ew")

        Entry(self, textvariable=self.server_ip, font=('Arial', 10, 'normal')).grid(row=1, column=0, sticky="ew", padx=10,
                                                                              pady=3, ipadx=3, ipady=3)
        Entry(self, textvariable=self.server_port, font=('Arial', 10, 'normal')).grid(row=3, column=0, sticky="ew", padx=10,
                                                                                pady=3, ipadx=3, ipady=3)
        Entry(self, textvariable=self.pieces_size, font=('Arial', 10, 'normal')).grid(row=5, column=0, sticky="ew", padx=10,
                                                                                pady=3, ipadx=3, ipady=3)

        submit_frame = Frame(self)
        submit_frame.grid(column=0, row=6, columnspan=2, pady=5, sticky="ew")

        submit_frame.grid_columnconfigure(0, weight=1)
        submit_frame.grid_columnconfigure(1, weight=1)
        submit_frame.grid_columnconfigure(2, weight=1)

        Button(submit_frame, text="Create torrent", bg="white", font=('Arial', 12), command=self.createTorrent).grid(column=1, row=0, sticky="ew")

    def createTorrent(self):
        self.parent.client.create_torrent_file(self.file_name,(self.server_ip.get(),
                                                int(self.server_port.get())), int(self.pieces_size.get()))

        self.parent.update()

        self.destroy()