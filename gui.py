import sys
import click
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
import os

import sys
print("Using Python executable:", sys.executable)

class SafetensorsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Safetensors Utility GUI")

        # Input file selection
        self.file_label = tk.Label(root, text="Select .safetensors file:")
        self.file_label.pack(pady=5)

        self.file_entry = tk.Entry(root, width=50)
        self.file_entry.pack(pady=5, padx=5)

        self.browse_button = tk.Button(root, text="Browse", command=self.browse_file)
        self.browse_button.pack(pady=5)

        # Command selection
        self.command_label = tk.Label(root, text="Select Command:")
        self.command_label.pack(pady=5)

        self.command_var = tk.StringVar()
        self.command_combobox = ttk.Combobox(
            root, textvariable=self.command_var, state="readonly"
        )
        self.command_combobox["values"] = (
            "checklora",
            "extractdata",
            "extracthdr",
            "header",
            "listkeys",
            "metadata",
            "writemd",
        )
        self.command_combobox.pack(pady=5)

        # Output display
        self.output_label = tk.Label(root, text="Output:")
        self.output_label.pack(pady=5)

        self.output_text = tk.Text(root, wrap=tk.WORD, height=15, width=60)
        self.output_text.pack(pady=5, padx=5)

        # Execute button
        self.execute_button = tk.Button(root, text="Execute", command=self.execute_command)
        self.execute_button.pack(pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Safetensors Files", "*.safetensors")]
        )
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)

    def execute_command(self):
        input_file = self.file_entry.get()
        command = self.command_var.get()

        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Error", "Please select a valid .safetensors file.")
            return

        if not command:
            messagebox.showerror("Error", "Please select a command.")
            return

        try:
            # Construct the command
            cmd = [sys.executable, "safetensors_util.py", command, input_file]

            # Run the command
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Display output or error
            self.output_text.delete("1.0", tk.END)
            if result.returncode == 0:
                self.output_text.insert(tk.END, result.stdout)
            else:
                self.output_text.insert(tk.END, result.stderr)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SafetensorsGUI(root)
    root.mainloop()
