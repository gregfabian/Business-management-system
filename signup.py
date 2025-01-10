import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import bcrypt

# Ensure the users table exists
conn = sqlite3.connect('business.db')
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
)
""")
conn.commit()

# Center the window at the middle of your screen
def center_window(window, width, height):
        """Centers the window on the screen."""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

class SignupPage:
    def __init__(self, root, on_success):
        self.root = root
        self.root.title("Sign Up")
        self.root.geometry("400x400")
        self.root.configure(bg="#426cf5")  # Set background color
        self.on_success = on_success
        self.create_widgets()
        center_window(self.root, 400, 400) # Call the center method

    def create_widgets(self):
        # Styling
        self.style = ttk.Style()
        self.style.configure("TButton",
                             background="#1abc9c",
                             foreground="black",
                             font=("times new roman", 12, "bold"),
                             padding=10)
        self.style.map("TButton",
                       background=[("active", "#16a085")],
                       foreground=[("active", "blue")])

        self.style.configure("TLabel", font=("times new roman", 12), background="#426cf5", foreground="white")
        self.style.configure("TEntry", font=("times new roman", 12))

        # Title
        self.title_label = tk.Label(self.root, text="Create Admin Account", font=("times new roman", 16, "bold"), bg="#426cf5", fg="white")
        self.title_label.pack(pady=20)

        # Username
        self.username_label = ttk.Label(self.root, text="Username:")
        self.username_entry = ttk.Entry(self.root, width=30)

        # Password
        self.password_label = ttk.Label(self.root, text="Password:")
        self.password_entry = ttk.Entry(self.root, width=30, show="*")

        # Buttons
        self.signup_button = ttk.Button(self.root, text="Sign Up", command=self.signup)
        self.back_to_login_button = ttk.Button(self.root, text="Back to Login", command=self.back_to_login)

        # Layout
        self.username_label.pack(pady=5)
        self.username_entry.pack(pady=5)
        self.password_label.pack(pady=5)
        self.password_entry.pack(pady=5)
        self.signup_button.pack(pady=10)
        self.back_to_login_button.pack(pady=5)

    def signup(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password")
            return

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            messagebox.showinfo("Success", "Account created successfully!")
            self.back_to_login()  # Go back to login after successful signup
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists. Please choose another.")

    def back_to_login(self):
        # Import LoginPage inside the method to avoid circular import
        from login import LoginPage
        # Destroy current signup window and create a new login window
        self.root.destroy()
        root = tk.Tk()
        LoginPage(root, self.on_success)
        root.mainloop()

    

