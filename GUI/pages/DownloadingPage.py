from time import sleep
from tkinter import *
from client import Client
from utils.threads import DownloadThread
from utils.threads.DownloadTask import DownloadStatus

UPDATE_FREQUENCY = 0.5

class DownloadingTaskPage(Frame):
    def __init__(self, parent, controller, client: Client):
        super().__init__(parent, padx=10, pady=20)
        self.controller = controller
        self.client = client

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        page_name = Label(self, text="Downloading Process", font=("Arial", 18), fg="#0388B4")
        page_name.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.update_button = Button(self, text="Update", command=self.update,
                                    fg="white", bg="#0388B4", font=("Arial", 10))
        self.update_button.grid(row=1, column=2, sticky="ew", pady=2, padx=2)

        self.download_frames = []

    def update(self):
        for download_frame in self.download_frames:
            download_frame.destroy()
        self.download_frames = [DownloadingFrame(self, download_task) for download_task in self.client.show_progress()]

        for idx, download_frame in enumerate(self.download_frames):
            download_frame.grid(row=idx+2, column=0, columnspan=3, sticky="ew", pady=2)
            download_frame.auto_update()

class DownloadingFrame(Frame):
    def __init__(self, parent, download_task: DownloadThread):
        super().__init__(parent, padx=5, pady=5, bg="white")
        self.parent = parent
        self.file_name = download_task.file_name
        self.key = download_task.file_id
        self.server_addr = download_task.server_conn.get_hostAddress()
        self.bit_string = "".join(download_task.bit_field)        # Bit string. Example: "111100000"
        self.status = download_task.status
        self.progress = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        Label(self, text=f"{self.server_addr} - {self.key}", font=('Arial', 8), fg='black', bg='white').grid(row=0, column=0, sticky="w")
        Label(self, text=self.file_name, font=('Arial', 12, 'bold'), fg='#0388B4', bg='white').grid(row=1, column=0, sticky="w", pady=5)
        Label(self, text=str(self.status), fg="gray", bg='white').grid(row=1, column=1, sticky='e')

    def auto_update(self) -> None:
        """
        Auto update the progress bar
        """
        self.update()

        while self.status == DownloadStatus.DOWNLOADING:
            sleep(1)
            download_task = self.parent.client.get_download_thread(self.key)
            self.bit_string = download_task.bit_field
            self.status = download_task.status

            self.update()
            sleep(1)

        self.update()

    def update(self):
        """
        Redraw the progress bar and status
        """
        self.draw_progress()
        Label(self, text=str(self.status), fg="gray", bg='white').grid(row=1, column=1, sticky='e')

    def draw_progress(self):
        self.update_idletasks()

        self.progress = ProgressBar(self, self.bit_string)
        self.progress.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.progress.draw(self.winfo_width())

class ProgressBar(Canvas):
    def __init__(self, parent, bit_string: str, height: int = 25):
        super().__init__(parent, width=400, height=height, bg="white", highlightthickness=1, highlightbackground="black")
        self.width = 0
        self.height = height
        self.bit_string = bit_string

    def draw(self, width):
        # self.update_idletasks()
        # self.width = self.winfo_width()
        self.width = width
        n_bits = len(self.bit_string)
        segment_width = self.width / n_bits  # Width of each segment

        for i, bit in enumerate(self.bit_string):
            segment_x1 = i * segment_width
            segment_x2 = segment_x1 + segment_width
            color = "green" if bit == '1' else "white"
            self.create_rectangle(segment_x1, 0, segment_x2, 25, fill=color, outline="white")