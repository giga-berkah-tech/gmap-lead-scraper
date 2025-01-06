import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd

class CSVViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Viewer")
        self.root.geometry("800x600")

        # Create a Frame for the treeview and scrollbar
        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Create a Treeview widget
        self.tree = ttk.Treeview(self.frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a vertical scrollbar to the treeview
        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a menu for opening files
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open CSV", command=self.open_csv)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)

    def open_csv(self):
        # Open a file dialog to select a CSV file
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.display_csv(file_path)

    def display_csv(self, file_path):
        # Clear any existing data in the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Load the CSV file into a pandas DataFrame
        df = pd.read_csv(file_path)

        # Set up the treeview columns
        self.tree["columns"] = list(df.columns)
        self.tree["show"] = "headings"
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.W)

        # Insert rows into the treeview
        for _, row in df.iterrows():
            self.tree.insert("", tk.END, values=list(row))

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVViewerApp(root)
    root.mainloop()
