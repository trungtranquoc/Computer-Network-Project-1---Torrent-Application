import tkinter as tk
from tkinter import ttk

from client import Client
from .pages import *


class App(tk.Tk):
    def __init__(self, client: Client):
        super().__init__()
        self.title(f"Client {client.get_ip_addr()}")

        # Run the client site
        self.client = client

        # Main layout: sidebar and content frame
        self.sidebar = ttk.Frame(self, width=150, relief="ridge", padding=2)
        self.sidebar.pack(side="left", fill="y")

        self.content = ttk.Frame(self, relief="ridge", padding=5)
        self.content.pack(side="right", expand=True, fill="both")

        # Store pages
        self.frames = {}

        # Add sidebar buttons
        self.add_sidebar_button("Directory", "DirectoryPage", 0)
        self.add_sidebar_button("Swarms Network", "NetworkPage", 1)
        self.add_sidebar_button("Local Swarms", "SwarmPage", 2)
        self.add_sidebar_button("Downloading Tasks", "DownloadingTaskPage", 3)

        # Initialize pages
        for Page in (NetworkPage, DownloadingTaskPage, DirectoryPage, SwarmPage):
            page_name = Page.__name__
            frame = Page(parent=self.content, controller=self, client=client)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="news")

        # Show the initial page
        self.show_frame("DirectoryPage")

    def add_sidebar_button(self, text, page_name, idx: int):
        """Create a button in the sidebar for navigation."""
        button = ttk.Button(self.sidebar, text=text, command=lambda: self.show_frame(page_name))
        button.grid(row=idx, column=0, sticky="news", ipady=10)

    def show_frame(self, page_name):
        """Show the selected page."""
        frame = self.frames[page_name]
        frame.tkraise()




