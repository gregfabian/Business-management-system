import tkinter as tk
from login import LoginPage
from dashboard import Dashboard

def show_dashboard():
    root = tk.Tk()
    dashboard = Dashboard(root)  # Initialize Dashboard (no show() needed)
    root.mainloop()

def main():
    """Start the Login page if user is not logged in"""
    root = tk.Tk()
    LoginPage(root, show_dashboard)
    root.mainloop()

if __name__ == "__main__":
    main()
