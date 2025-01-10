import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import bcrypt

# Database setup (to make sure the users table is created)
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


class LoginPage:
    def __init__(self, root, on_success):
        self.root = root
        self.root.title("Login")
        # self.root.geometry("400x400")
        self.root.configure(bg="#426cf5")  # Set background color
        self.on_success = on_success
        self.create_widgets()
        center_window(self.root, 400, 400)  # Call the center method

    def create_widgets(self):
        # Styling
        self.style = ttk.Style()
        self.style.configure("TButton",
                             background="#3498db",
                             foreground="black",
                             font=("Arial", 12, "bold"),
                             padding=10)
        self.style.map("TButton",
                       background=[("active", "#2980b9")],
                       foreground=[("active", "blue")])

        self.style.configure("TLabel", font=("times new roman", 12), background="#426cf5", foreground="white")
        self.style.configure("TEntry", font=("times new roman", 12))

        # Title
        self.title_label = tk.Label(self.root, text="Admin Login", font=("times new roman", 16, "bold"), bg="#426cf5", fg="white")
        self.title_label.pack(pady=20)

        # Username
        self.username_label = ttk.Label(self.root, text="Username:")
        self.username_entry = ttk.Entry(self.root, width=30)

        # Password
        self.password_label = ttk.Label(self.root, text="Password:")
        self.password_entry = ttk.Entry(self.root, width=30, show="*")

        # Buttons
        self.login_button = ttk.Button(self.root, text="Login",command=self.login)
        self.signup_button = ttk.Button(self.root, text="Sign Up", command=self.signup)

        # Layout
        self.username_label.pack(pady=5)
        self.username_entry.pack(pady=5)
        self.password_label.pack(pady=5)
        self.password_entry.pack(pady=5)
        self.login_button.pack(pady=10)
        self.signup_button.pack(pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password")
            return

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            stored_password = user[1]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                messagebox.showinfo("Login Success", "Logged in successfully!")
                self.root.destroy()
                self.on_success()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password")
        else:
            messagebox.showerror("Login Failed", "User does not exist")

    def signup(self):
        # Import SignupPage inside the method to avoid circular import
        from signup import SignupPage  # Importing here to avoid circular import
        # Destroy current login window and create a new signup window
        self.root.destroy()
        root = tk.Tk()
        SignupPage(root, self.on_success)  # Pass on_success to SignupPage
        root.mainloop()
