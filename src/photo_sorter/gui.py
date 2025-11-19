import tkinter as tk

def run():
    """Start the main window of the PhotoSorter application."""
    root = tk.Tk()
    root.title("PhotoSorter - MVP")
    root.geometry("800x600")

    label = tk.Label(
        root,
        text="PhotoSorter - okienko startowe",
        font=("Arial",14),
    )  

    label.pack(pady=20)

    root.mainloop()