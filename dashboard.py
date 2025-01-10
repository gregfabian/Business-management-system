import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import sqlite3
from tkinter.simpledialog import askstring  # For user input of the date

# Database connection
conn = sqlite3.connect("business.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

# Create necessary tables
def create_tables():
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT,
        total_spent REAL DEFAULT 0
    )
    ''')    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            price REAL,
            quantity INTEGER,
            image BLOB
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total_price REAL,
            order_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY,
            name TEXT,
            role TEXT,
            phone TEXT,
            email TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER PRIMARY KEY,
            name TEXT,
            contact TEXT,
            product_supplied INTEGER,
            FOREIGN KEY (product_supplied) REFERENCES products (product_id) ON DELETE SET NULL
        )
    ''')

    # Views
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS sales_summary AS
    SELECT 
        o.order_date AS order_date,
        SUM(o.total_price) AS total_sales
    FROM orders o
    GROUP BY o.order_date
    """)

    cursor.execute("""
        CREATE VIEW IF NOT EXISTS stock_summary AS
        SELECT 
            p.name AS product_name,
            SUM(o.quantity) AS total_sold
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        GROUP BY p.name
    """)

    cursor.execute("""
        CREATE VIEW IF NOT EXISTS customer_spending_summary AS
        SELECT 
            c.name AS customer_name,
            SUM(o.total_price) AS total_spent
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.name
    """)

    # Triggers
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_customer_total_spent
    AFTER INSERT ON orders
    FOR EACH ROW
    BEGIN
        UPDATE customers
        SET total_spent = (SELECT SUM(total_price) FROM orders WHERE customer_id = NEW.customer_id)
        WHERE customer_id = NEW.customer_id;
    END;
    ''')

    """Create a trigger to update the product stock when an order is made."""
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_product_stock
        AFTER INSERT ON orders
        FOR EACH ROW
        BEGIN
            UPDATE products
            SET quantity = quantity - NEW.quantity
            WHERE product_id = NEW.product_id;
        END;
    """)

    conn.commit()

create_tables()




# Initialize Tkinter window
class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root = root
        self.root.title("Admin Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f8f9fa")
        self.create_widgets()

        # Create a style object
        self.style = ttk.Style()

        # TButton Style (Normal State and Active/Hover State)
        self.style.configure("TButton",
                             background="blue",   # Green background
                             foreground="black",     # Text color
                             font=("times new roman", 12),      # Font style and size
                             padding=10,             # Padding for better space
                             relief="flat",          # Flat style for buttons
                             anchor="center")        # Center text inside the button

        # Style for TButton on hover (active state)
        self.style.map("TButton",
                       foreground=[("active", "blue")],  # White text when hovering
                       background=[("active", "#45a049")],  # Darker green background when hovering
                       )

        # TTreeview Style
        self.style.configure("TTreeview",
                             font=("times new roman", 10),
                             rowheight=30)  # Row height for treeview items

        # Treeview Heading Style
        self.style.configure("TTreeview.Heading",
                             font=("times new roman", 12, "bold"),
                             background="#f0f0f0",
                             foreground="black")

        # Style for Notebook tabs
        self.style.configure("TNotebook",
                             background="#f0f0f0")

        self.style.configure("TNotebook.Tab",
                             padding=10,
                             font=("times new roman", 12),
                             background="#f0f0f0",
                             foreground="black")

        self.style.map("TNotebook.Tab",
                       background=[("selected", "#e7e7e7")],
                       foreground=[("selected", "black")])
        
    def create_widgets(self):
        # Create a Notebook widget
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)
        
        # Background color for all tabs
        # tab_bg_color_product = "#f78fce"
        tab_bg_color_product = "#426cf5"
        tab_bg_color_customer = "#426cf5"
        tab_bg_color_employee = "#426cf5"
        tab_bg_color_order = "#426cf5"
        tab_bg_color_supplier = "#426cf5"
        tab_bg_color_analytics = "#426cf5"

        # Create tabs for different sections of the dashboard
        self.product_management_frame = tk.Frame(self.notebook, bg=tab_bg_color_product)
        self.customer_management_frame = tk.Frame(self.notebook, bg=tab_bg_color_customer)
        self.employee_management_frame = tk.Frame(self.notebook, bg=tab_bg_color_employee)
        self.order_management_frame = tk.Frame(self.notebook, bg=tab_bg_color_order)
        self.supplier_management_frame = tk.Frame(self.notebook, bg=tab_bg_color_supplier)
        self.analytics_frame = tk.Frame(self.notebook, bg=tab_bg_color_analytics)

        # Add tabs
        self.notebook.add(self.product_management_frame, text="Product Management")
        self.notebook.add(self.customer_management_frame, text="Customer Management")
        self.notebook.add(self.employee_management_frame, text="Employee Management")
        self.notebook.add(self.order_management_frame, text="Order Management")
        self.notebook.add(self.supplier_management_frame, text="Supplier Management")
        self.notebook.add(self.analytics_frame, text="Analytics")

        # Initialize all management sections
        self.product_management = ProductManagement(self.product_management_frame)
        self.customer_management = CustomerManagement(self.customer_management_frame)
        self.employee_management = EmployeeManagement(self.employee_management_frame)
        self.order_management = OrderManagement(self.order_management_frame)
        self.supplier_management = SupplierManagement(self.supplier_management_frame)
        self.analytics = Analytics(self.analytics_frame)

class ProductManagement:
    def __init__(self, frame):
        self.frame = frame
        self.selected_image_path = None
        self.create_widgets()

    def create_widgets(self):
        self.product_name_label = tk.Label(self.frame, text="Product Name:", font=("times new roman", 12, "bold"))
        self.product_name = tk.Entry(self.frame)
        self.price_label = tk.Label(self.frame, text="Price:", font=("times new roman", 12, "bold"))
        self.price = tk.Entry(self.frame)
        self.stock_label = tk.Label(self.frame, text="Stock:", font=("times new roman", 12, "bold"))
        self.stock = tk.Entry(self.frame)

        self.add_product_button = ttk.Button(self.frame, text="Add Product", command=self.add_product)
        self.view_product_button = ttk.Button(self.frame, text="View Products", command=self.view_products)
        self.upload_image_button = ttk.Button(self.frame, text="Upload Image", command=self.upload_image)
        self.delete_product_button = ttk.Button(self.frame, text="Delete Product", command=self.delete_product)
        self.update_product_button = ttk.Button(self.frame, text="Update Product", command=self.update_product)

        self.image_label = tk.Label(self.frame, text="No image selected", width=40, height=5, relief="sunken")

        # Layout
        self.product_name_label.grid(row=1, column=0, padx=10, pady=10)
        self.product_name.grid(row=1, column=1, padx=10, pady=10)
        self.price_label.grid(row=2, column=0, padx=10, pady=10)
        self.price.grid(row=2, column=1, padx=10, pady=10)
        self.stock_label.grid(row=3, column=0, padx=10, pady=10)
        self.stock.grid(row=3, column=1, padx=10, pady=10)

        self.upload_image_button.grid(row=4, column=0, padx=2, pady=10)
        self.image_label.grid(row=4, column=1, padx=2, pady=10)

        self.add_product_button.grid(row=5, column=0,  pady=15)
        self.view_product_button.grid(row=5, column=1,  pady=15)
        self.delete_product_button.grid(row=5, column=2, pady=15)
        self.update_product_button.grid(row=5, column=3, pady=15)

        # Scrollbar
        self.tree_frame = tk.Frame(self.frame)
        self.tree_frame.grid(row=9, column=0, columnspan=4, padx=10, pady=10)

        # Treeview
        self.tree = ttk.Treeview(self.tree_frame, columns=("Product ID", "Product Name", "Price", "Stock", "Image"), show="headings")
        self.tree.heading("Product ID", text="Product ID")
        self.tree.heading("Product Name", text="Product Name")
        self.tree.heading("Price", text="Price")
        self.tree.heading("Stock", text="Stock")
        self.tree.heading("Image", text="Image")
        self.tree.grid(row=0, column=0, padx=10, pady=10)

        # Vertical Scrollbar
        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.config(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.grid(row=0, column=1, sticky="ns")

        self.view_products()  # Load products on startup


        

    def upload_image(self):
        """Open a file dialog to select an image"""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.gif")])
        if file_path:
            self.selected_image_path = file_path
            image = Image.open(file_path)
            image = image.resize((100, 100), Image.Resampling.LANCZOS)  # Resize image
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo, text="")  # Set image and clear text
            self.image_label.image = photo  # Keep reference to image to avoid garbage collection

    def add_product(self):
        """Insert product data into the database after checking for duplicates."""
        name = self.product_name.get()
        price = self.price.get()
        stock = self.stock.get()

        if not all([name, price, stock]):
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        # Check if a product with the same name already exists
        cursor.execute("SELECT COUNT(*) FROM products WHERE name = ?", (name,))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror("Duplicate Entry", f"A product with the name '{name}' already exists. Please use a unique name.")
            return

        # Insert product data with image path (not storing the image itself in the database)
        image_path = self.selected_image_path if self.selected_image_path else "No image selected"

        cursor.execute("""INSERT INTO products (name, price, quantity, image)
                        VALUES (?, ?, ?, ?)""", (name, price, stock, image_path))
        conn.commit()
        messagebox.showinfo("Success", "Product added successfully!")
        self.view_products()

    def view_products(self):
        """Display all products in the Treeview widget"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4]))

    def delete_product(self):
        """Delete the selected product from the database"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a product to delete.")
            return
        
        product_id = self.tree.item(selected_item)["values"][0]
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        messagebox.showinfo("Success", f"Product with ID {product_id} deleted successfully!")
        self.view_products()

    def update_product(self):
        """Update the selected product's data in the database"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a product to update.")
            return

        product_id = self.tree.item(selected_item)["values"][0]
        name = self.product_name.get()
        price = self.price.get()
        stock = self.stock.get()
        image_path = self.selected_image_path if self.selected_image_path else "No image selected"

        if not all([name, price, stock]):
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        cursor.execute("""UPDATE products
                          SET name = ?, price = ?, quantity = ?, image = ?
                          WHERE product_id = ?""",
                       (name, price, stock, image_path, product_id))
        conn.commit()
        messagebox.showinfo("Success", f"Product ID {product_id} updated successfully!")
        self.view_products()

class CustomerManagement:
    def __init__(self, frame):
        self.frame = frame
        self.create_widgets()

    def create_widgets(self):
        # Labels and Entry fields
        self.customer_name_label = tk.Label(self.frame, text="Customer Name:", font=("times new roman", 12, "bold"))
        self.customer_name = tk.Entry(self.frame)
        self.customer_phone_label = tk.Label(self.frame, text="Phone:", font=("times new roman", 12, "bold"))
        self.customer_phone = tk.Entry(self.frame)
        self.customer_email_label = tk.Label(self.frame, text="Email:", font=("times new roman", 12, "bold"))
        self.customer_email = tk.Entry(self.frame)

        # Buttons for CRUD operations
        self.add_customer_button = ttk.Button(self.frame, text="Add Customer", command=self.add_customer)
        self.view_customer_button = ttk.Button(self.frame, text="View Customers", command=self.view_customers)
        self.update_customer_button = ttk.Button(self.frame, text="Update Customer", command=self.update_customer)
        self.delete_customer_button = ttk.Button(self.frame, text="Delete Customer", command=self.delete_customer)

        # Layout for labels, entries, and buttons
        self.customer_name_label.grid(row=1, column=0, padx=10, pady=10)
        self.customer_name.grid(row=1, column=1, padx=10, pady=10)
        self.customer_phone_label.grid(row=2, column=0, padx=10, pady=10)
        self.customer_phone.grid(row=2, column=1, padx=10, pady=10)
        self.customer_email_label.grid(row=3, column=0, padx=10, pady=10)
        self.customer_email.grid(row=3, column=1, padx=10, pady=10)

        self.add_customer_button.grid(row=4, column=0, pady=15)
        self.view_customer_button.grid(row=4, column=1, pady=15)
        self.update_customer_button.grid(row=4, column=2, pady=15)
        self.delete_customer_button.grid(row=4, column=4, pady=15)

        # Scrollbar and Treeview for displaying customers
        self.tree_frame = tk.Frame(self.frame)
        self.tree_frame.grid(row=8, column=0, columnspan=4, padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Customer ID", "Name", "Phone", "Email", "Total Spent"), show="headings")
        self.tree.heading("Customer ID", text="Customer ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Phone", text="Phone")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Total Spent", text="Total Spent")
        self.tree.grid(row=0, column=0, padx=10, pady=10)

        # Vertical scrollbar
        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.config(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.grid(row=0, column=1, sticky="ns")

        # Initial call to view customers
        self.view_customers()

    def add_customer(self):
        """Insert customer data into the database"""
        name = self.customer_name.get()
        phone = self.customer_phone.get()
        email = self.customer_email.get()

        if not all([name, phone, email]):
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        cursor.execute("""
            INSERT INTO customers (name, phone, email)
            VALUES (?, ?, ?)
        """, (name, phone, email))
        conn.commit()
        messagebox.showinfo("Success", "Customer added successfully!")
        self.view_customers()

    def view_customers(self):
        """Display all customers in the Treeview widget"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        cursor.execute("SELECT * FROM customers")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4]))  # Display total_spent

    def update_customer(self):
        """Update selected customer's details"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a customer to update.")
            return

        customer_id = self.tree.item(selected_item)["values"][0]
        name = self.customer_name.get()
        phone = self.customer_phone.get()
        email = self.customer_email.get()

        if not all([name, phone, email]):
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        cursor.execute("""
            UPDATE customers
            SET name = ?, phone = ?, email = ?
            WHERE customer_id = ?
        """, (name, phone, email, customer_id))
        conn.commit()
        messagebox.showinfo("Success", f"Customer ID {customer_id} updated successfully!")
        self.view_customers()

    def delete_customer(self):
        """Delete selected customer from the database"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a customer to delete.")
            return

        customer_id = self.tree.item(selected_item)["values"][0]
        cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
        conn.commit()
        messagebox.showinfo("Success", f"Customer ID {customer_id} deleted successfully!")
        self.view_customers()

class EmployeeManagement:
    def __init__(self, frame):
        self.frame = frame
        self.create_widgets()

    def create_widgets(self):
        # Labels and Entry fields
        self.employee_name_label = tk.Label(self.frame, text="Employee Name:", font=("times new roman", 12, "bold"))
        self.employee_name = tk.Entry(self.frame)
        self.employee_role_label = tk.Label(self.frame, text="Role:", font=("times new roman", 12, "bold"))
        self.employee_role = tk.Entry(self.frame)
        self.employee_phone_label = tk.Label(self.frame, text="Phone:", font=("times new roman", 12, "bold"))
        self.employee_phone = tk.Entry(self.frame)
        self.employee_email_label = tk.Label(self.frame, text="Email:", font=("times new roman", 12, "bold"))
        self.employee_email = tk.Entry(self.frame)

        # Buttons for CRUD operations
        self.add_employee_button = ttk.Button(self.frame, text="Add Employee", command=self.add_employee)
        self.update_employee_button = ttk.Button(self.frame, text="Update Employee", command=self.update_employee)
        self.delete_employee_button = ttk.Button(self.frame, text="Delete Employee", command=self.delete_employee)
        self.view_employee_button = ttk.Button(self.frame, text="View Employees", command=self.view_employees)

        # Layout for labels, entries, and buttons
        self.employee_name_label.grid(row=1, column=0, padx=10, pady=10)
        self.employee_name.grid(row=1, column=1, padx=10, pady=10)
        self.employee_role_label.grid(row=2, column=0, padx=10, pady=10)
        self.employee_role.grid(row=2, column=1, padx=10, pady=10)
        self.employee_phone_label.grid(row=3, column=0, padx=10, pady=10)
        self.employee_phone.grid(row=3, column=1, padx=10, pady=10)
        self.employee_email_label.grid(row=4, column=0, padx=10, pady=10)
        self.employee_email.grid(row=4, column=1, padx=10, pady=10)

        self.add_employee_button.grid(row=5, column=0,  pady=15)
        self.update_employee_button.grid(row=5, column=1, pady=15)
        self.delete_employee_button.grid(row=5, column=2,  pady=15)
        self.view_employee_button.grid(row=5, column=3,  pady=15)

        # Treeview and Scrollbar
        self.tree_frame = tk.Frame(self.frame)
        self.tree_frame.grid(row=9, column=0, columnspan=4, padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Employee ID", "Name", "Role", "Phone", "Email"), show="headings")
        self.tree.heading("Employee ID", text="Employee ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Role", text="Role")
        self.tree.heading("Phone", text="Phone")
        self.tree.heading("Email", text="Email")
        self.tree.grid(row=0, column=0, padx=10, pady=10)

        # Vertical scrollbar
        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.config(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.grid(row=0, column=1, sticky="ns")

        # Load employees on startup
        self.view_employees()

    def add_employee(self):
        """Add a new employee to the database."""
        name = self.employee_name.get()
        role = self.employee_role.get()
        phone = self.employee_phone.get()
        email = self.employee_email.get()

        if not all([name, role, phone, email]):
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        cursor.execute("""
            INSERT INTO employees (name, role, phone, email)
            VALUES (?, ?, ?, ?)
        """, (name, role, phone, email))
        conn.commit()
        messagebox.showinfo("Success", "Employee added successfully!")
        self.view_employees()

    def view_employees(self):
        """Display all employees in the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        cursor.execute("SELECT * FROM employees")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", "end", values=row)

    def update_employee(self):
        """Update details of the selected employee."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select an employee to update.")
            return

        employee_id = self.tree.item(selected_item)["values"][0]
        name = self.employee_name.get()
        role = self.employee_role.get()
        phone = self.employee_phone.get()
        email = self.employee_email.get()

        if not all([name, role, phone, email]):
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        cursor.execute("""
            UPDATE employees
            SET name = ?, role = ?, phone = ?, email = ?
            WHERE employee_id = ?
        """, (name, role, phone, email, employee_id))
        conn.commit()
        messagebox.showinfo("Success", f"Employee ID {employee_id} updated successfully!")
        self.view_employees()

    def delete_employee(self):
        """Delete the selected employee."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select an employee to delete.")
            return

        employee_id = self.tree.item(selected_item)["values"][0]
        cursor.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
        conn.commit()
        messagebox.showinfo("Success", f"Employee ID {employee_id} deleted successfully!")
        self.view_employees()

class OrderManagement:
    def __init__(self, frame):
        self.frame = frame
        self.create_widgets()

    def create_widgets(self):
        # Labels and Entry fields
        self.customer_id_label = tk.Label(self.frame, text="Customer ID:", font=("times new roman", 12, "bold"))
        self.customer_id = tk.Entry(self.frame)
        self.product_id_label = tk.Label(self.frame, text="Product ID:", font=("times new roman", 12, "bold"))
        self.product_id = tk.Entry(self.frame)
        self.quantity_label = tk.Label(self.frame, text="Quantity:", font=("times new roman", 12, "bold"))
        self.quantity = tk.Entry(self.frame)
        self.price_label = tk.Label(self.frame, text="Price:", font=("times new roman", 12, "bold"))
        self.price = tk.Entry(self.frame)
        self.date_label = tk.Label(self.frame, text="Date (Format: YYYY-MM-DD):", font=("times new roman", 12, "bold"))
        self.date = tk.Entry(self.frame)

        # Buttons for CRUD operations
        self.add_order_button = ttk.Button(self.frame, text="Add Order", command=self.add_order)
        self.update_order_button = ttk.Button(self.frame, text="Update Order", command=self.update_order)
        self.delete_order_button = ttk.Button(self.frame, text="Delete Order", command=self.delete_order)
        self.view_order_button = ttk.Button(self.frame, text="View Orders", command=self.view_orders)

        # Layout for labels, entries, and buttons
        self.customer_id_label.grid(row=1, column=0, padx=10, pady=10)
        self.customer_id.grid(row=1, column=1, padx=10, pady=10)
        self.product_id_label.grid(row=2, column=0, padx=10, pady=10)
        self.product_id.grid(row=2, column=1, padx=10, pady=10)
        self.quantity_label.grid(row=3, column=0, padx=10, pady=10)
        self.quantity.grid(row=3, column=1, padx=10, pady=10)
        self.price_label.grid(row=4, column=0, padx=10, pady=10)
        self.price.grid(row=4, column=1, padx=10, pady=10)
        self.date_label.grid(row=5, column=0, padx=10, pady=10)
        self.date.grid(row=5, column=1, padx=10, pady=10)

        self.add_order_button.grid(row=6, column=0, pady=15)
        self.update_order_button.grid(row=6, column=1, pady=15)
        self.delete_order_button.grid(row=6, column=2, pady=15)
        self.view_order_button.grid(row=6, column=3, pady=15)

        # Treeview and Scrollbar
        self.tree_frame = tk.Frame(self.frame)
        self.tree_frame.grid(row=10, column=0, columnspan=4, padx=10, pady=10)

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("Order ID", "Customer ID", "Product ID", "Quantity", "Total Price", "Date"),
            show="headings"
        )
        self.tree.heading("Order ID", text="Order ID")
        self.tree.heading("Customer ID", text="Customer ID")
        self.tree.heading("Product ID", text="Product ID")
        self.tree.heading("Quantity", text="Quantity")
        self.tree.heading("Total Price", text="Total Price")
        self.tree.heading("Date", text="Date")

        self.tree.grid(row=0, column=0, sticky="nsew")

        # Add vertical scrollbar
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.config(yscrollcommand=self.tree_scroll_y.set)
        self.tree_scroll_y.grid(row=0, column=1, sticky="ns")

        # Add horizontal scrollbar
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.config(xscrollcommand=self.tree_scroll_x.set)
        self.tree_scroll_x.grid(row=1, column=0, sticky="ew")

        # Configure grid for resizing
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        # Load orders on startup
        self.view_orders()

    def validate_inputs(self, *inputs):
        """Validate that all inputs are provided."""
        for input_value in inputs:
            if not input_value.strip():
                messagebox.showwarning("Input Error", "All fields are required. Please fill in all fields.")
                return False
        return True

    def validate_product_details(self, product_id, price, quantity):
        """Validate product price and stock."""
        cursor.execute("SELECT price, quantity FROM products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            messagebox.showerror("Validation Error", "Product ID does not exist.")
            return False

        db_price, db_quantity = product

        if float(price) != db_price:
            messagebox.showerror("Validation Error", f"Price mismatch! Expected: {db_price}, Entered: {price}")
            return False

        if int(quantity) > db_quantity:
            messagebox.showerror(
                "Validation Error", f"Insufficient stock! Available quantity: {db_quantity}, Entered: {quantity}"
            )
            return False

        if int(quantity) <= 0:
            messagebox.showerror("Validation Error", "Quantity must be greater than zero.")
            return False

        return True

    def add_order(self):
        """Add a new order to the database."""
        customer_id = self.customer_id.get()
        product_id = self.product_id.get()
        quantity = self.quantity.get()
        price = self.price.get()
        order_date = self.date.get()

        if not self.validate_inputs(customer_id, product_id, quantity, price, order_date):
            return

        if not self.validate_references(customer_id, product_id):
            return

        if not self.validate_product_details(product_id, price, quantity):
            return

        # Insert order into the database
        cursor.execute("""
            INSERT INTO orders (customer_id, product_id, quantity, total_price, order_date)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, product_id, quantity, float(price) * int(quantity), order_date))
        conn.commit()
        messagebox.showinfo("Success", "Order added successfully!")
        self.view_orders()

    def view_orders(self):
        """Display all orders in the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        cursor.execute("SELECT * FROM orders")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", "end", values=row)


    def validate_references(self, customer_id, product_id):
        """Validate that customer_id exists in the customers table and product_id exists in the products table."""
        # Validate customer_id
        cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        customer = cursor.fetchone()
        if not customer:
            messagebox.showerror("Validation Error", "Customer ID does not exist.")
            return False

        # Validate product_id
        cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            messagebox.showerror("Validation Error", "Product ID does not exist.")
            return False

        return True


    def update_order(self):
        """Update details of the selected order."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select an order to update.")
            return

        order_id = self.tree.item(selected_item)["values"][0]
        customer_id = self.customer_id.get()
        product_id = self.product_id.get()
        quantity = self.quantity.get()
        price = self.price.get()
        order_date = self.date.get()

        if not self.validate_inputs(customer_id, product_id, quantity, price, order_date):
            return

        if not self.validate_references(customer_id, product_id):
            return

        if not self.validate_product_details(product_id, price, quantity):
            return

        # Update order in the database
        cursor.execute("""
            UPDATE orders
            SET customer_id = ?, product_id = ?, quantity = ?, total_price = ?, order_date = ?
            WHERE order_id = ?
        """, (customer_id, product_id, quantity, float(price) * int(quantity), order_date, order_id))
        conn.commit()
        messagebox.showinfo("Success", f"Order ID {order_id} updated successfully!")
        self.view_orders()

    def delete_order(self):
        """Delete the selected order."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select an order to delete.")
            return

        order_id = self.tree.item(selected_item)["values"][0]
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
        messagebox.showinfo("Success", f"Order ID {order_id} deleted successfully!")
        self.view_orders()



class SupplierManagement:
    def __init__(self, frame):
        self.frame = frame
        self.create_widgets()

    def create_widgets(self):
        # Labels and Entry fields
        self.supplier_name_label = tk.Label(self.frame, text="Supplier Name:", font=("times new roman", 12, "bold"))
        self.supplier_name = tk.Entry(self.frame)
        self.supplier_contact_label = tk.Label(self.frame, text="Contact:", font=("times new roman", 12, "bold"))
        self.supplier_contact = tk.Entry(self.frame)
        self.product_supplied_label = tk.Label(self.frame, text="Product Supplied (ID):", font=("times new roman", 12, "bold"))
        self.product_supplied = tk.Entry(self.frame)

        # Buttons for CRUD operations
        self.add_supplier_button = ttk.Button(self.frame, text="Add Supplier", command=self.add_supplier)
        self.update_supplier_button = ttk.Button(self.frame, text="Update Supplier", command=self.update_supplier)
        self.delete_supplier_button = ttk.Button(self.frame, text="Delete Supplier", command=self.delete_supplier)
        self.view_supplier_button = ttk.Button(self.frame, text="View Suppliers", command=self.view_suppliers)

        # Layout for labels, entries, and buttons
        self.supplier_name_label.grid(row=1, column=0, padx=10, pady=10)
        self.supplier_name.grid(row=1, column=1, padx=10, pady=10)
        self.supplier_contact_label.grid(row=2, column=0, padx=10, pady=10)
        self.supplier_contact.grid(row=2, column=1, padx=10, pady=10)
        self.product_supplied_label.grid(row=3, column=0, padx=10, pady=10)
        self.product_supplied.grid(row=3, column=1, padx=10, pady=10)

        self.add_supplier_button.grid(row=4, column=0, pady=15)
        self.update_supplier_button.grid(row=4, column=1, pady=15)
        self.delete_supplier_button.grid(row=4, column=2, pady=15)
        self.view_supplier_button.grid(row=4, column=3, pady=15)

        # Treeview and Scrollbar
        self.tree_frame = tk.Frame(self.frame)
        self.tree_frame.grid(row=8, column=0, columnspan=4, padx=10, pady=10)

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("Supplier ID", "Name", "Contact", "Product Supplied"),
            show="headings"
        )
        self.tree.heading("Supplier ID", text="Supplier ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Contact", text="Contact")
        self.tree.heading("Product Supplied", text="Product Supplied")

        self.tree.grid(row=0, column=0, sticky="nsew")

        # Add vertical scrollbar
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.config(yscrollcommand=self.tree_scroll_y.set)
        self.tree_scroll_y.grid(row=0, column=1, sticky="ns")

        # Add horizontal scrollbar
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.config(xscrollcommand=self.tree_scroll_x.set)
        self.tree_scroll_x.grid(row=1, column=0, sticky="ew")

        # Configure grid for resizing
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        # Load suppliers on startup
        self.view_suppliers()

    def add_supplier(self):
        """Add a new supplier to the database."""
        name = self.supplier_name.get()
        contact = self.supplier_contact.get()
        product_supplied = self.product_supplied.get()

        if not all([name, contact, product_supplied]):
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        # Ensure product_supplied exists in the products table
        cursor.execute("SELECT product_id FROM products WHERE product_id = ?", (product_supplied,))
        if cursor.fetchone() is None:
            messagebox.showwarning("Validation Error", "Invalid Product ID. Please enter a valid product.")
            return

        cursor.execute("""
            INSERT INTO suppliers (name, contact, product_supplied)
            VALUES (?, ?, ?)
        """, (name, contact, product_supplied))
        conn.commit()
        messagebox.showinfo("Success", "Supplier added successfully!")
        self.view_suppliers()

    def update_supplier(self):
        """Update details of the selected supplier."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a supplier to update.")
            return

        supplier_id = self.tree.item(selected_item)["values"][0]
        name = self.supplier_name.get()
        contact = self.supplier_contact.get()
        product_supplied = self.product_supplied.get()

        if not all([name, contact, product_supplied]):
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        # Ensure product_supplied exists in the products table
        cursor.execute("SELECT product_id FROM products WHERE product_id = ?", (product_supplied,))
        if cursor.fetchone() is None:
            messagebox.showwarning("Validation Error", "Invalid Product ID. Please enter a valid product.")
            return

        cursor.execute("""
            UPDATE suppliers
            SET name = ?, contact = ?, product_supplied = ?
            WHERE supplier_id = ?
        """, (name, contact, product_supplied, supplier_id))
        conn.commit()
        messagebox.showinfo("Success", f"Supplier ID {supplier_id} updated successfully!")
        self.view_suppliers()

    def delete_supplier(self):
        """Delete the selected supplier."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a supplier to delete.")
            return

        supplier_id = self.tree.item(selected_item)["values"][0]
        cursor.execute("DELETE FROM suppliers WHERE supplier_id = ?", (supplier_id,))
        conn.commit()
        messagebox.showinfo("Success", f"Supplier ID {supplier_id} deleted successfully!")
        self.view_suppliers()

    def view_suppliers(self):
        """Display all suppliers in the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        cursor.execute("SELECT * FROM suppliers")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", "end", values=row)



# The Analytics class
class Analytics:
    def __init__(self, frame):
        self.frame = frame
        self.create_widgets()

    def create_widgets(self):
        # Threshold labels and entry fields with descriptive text
        self.sales_threshold_label = tk.Label(
            self.frame, 
            text="Order Threshold: Show only dates where total sales exceed this amount."
        , font=("times new roman", 12, "bold"))
        self.sales_threshold = tk.Entry(self.frame)
        self.sales_threshold.insert(0, "1000")  # Default value

        self.stock_threshold_label = tk.Label(
            self.frame, 
            text="stock Threshold: Show only products where sold quantity exceeds this amount."
        , font=("times new roman", 12, "bold"))
        self.stock_threshold = tk.Entry(self.frame)
        self.stock_threshold.insert(0, "50")  # Default value

        self.customer_threshold_label = tk.Label(
            self.frame, 
            text="Customer Spending Threshold: Show only customers who spent more than this amount."
        , font=("times new roman", 12, "bold"))
        self.customer_threshold = tk.Entry(self.frame)
        self.customer_threshold.insert(0, "500")  # Default value

        # Buttons for generating reports
        self.sales_report_button = ttk.Button(
            self.frame, text="Generate Sales Report", style="TButton", command=self.view_sales_report
        )
        self.stock_report_button = ttk.Button(
            self.frame, text="Generate stock Report", style="TButton", command=self.view_stock_report
        )
        self.top_customers_button = ttk.Button(
            self.frame, text="Generate Top Customers Report", style="TButton", command=self.view_top_customers
        )
        self.order_summary_report_button = ttk.Button(
            self.frame, text="Generate Order Summary Report", style="TButton", command=self.view_order_summary_report
        )

        # Layout
        self.sales_threshold_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.sales_threshold.grid(row=0, column=1, padx=10, pady=5)
        self.sales_report_button.grid(row=0, column=2, padx=10, pady=5)

        self.stock_threshold_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.stock_threshold.grid(row=1, column=1, padx=10, pady=5)
        self.stock_report_button.grid(row=1, column=2, padx=10, pady=5)

        self.customer_threshold_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.customer_threshold.grid(row=2, column=1, padx=10, pady=5)
        self.top_customers_button.grid(row=2, column=2, padx=10, pady=5)

        self.order_summary_report_button.grid(row=3, column=0, padx=10, pady=5, columnspan=3)

    def calculate_total_sales_for_date(self, order_date):
        """Reusable function to calculate total sales for a given date."""
        cursor.execute("""
            SELECT SUM(total_price)
            FROM orders
            WHERE order_date = ?
        """, (order_date,))
        result = cursor.fetchone()
        return result[0] if result[0] else 0

    def view_sales_report(self):
        try:
            sales_threshold = float(self.sales_threshold.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number for Sales Threshold.")
            return

        cursor.execute("""
            SELECT order_date, total_sales
            FROM sales_summary
            WHERE total_sales > ?
            ORDER BY order_date ASC
        """, (sales_threshold,))
        rows = cursor.fetchall()

        if not rows:
            messagebox.showinfo("Sales Report", "No sales data above the threshold.")
            return

        report = f"Sales Report (Threshold: {sales_threshold}):\n"
        for row in rows:
            report += f"Date: {row[0]}, Total Sales: {row[1]:.2f}\n"
        messagebox.showinfo("Sales Report", report)

    def view_stock_report(self):
        try:
            stock_threshold = int(self.stock_threshold.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number for stock Threshold.")
            return

        cursor.execute("""
            SELECT product_name, total_sold
            FROM stock_summary
            WHERE total_sold > ?
            ORDER BY total_sold DESC
        """, (stock_threshold,))
        rows = cursor.fetchall()

        if not rows:
            messagebox.showinfo("stock Report", "No products sold above the threshold.")
            return

        report = f"stock Report (Threshold: {stock_threshold}):\n"
        for row in rows:
            report += f"Product: {row[0]}, Total Sold: {row[1]}\n"
        messagebox.showinfo("stock Report", report)

    def view_top_customers(self):
        try:
            customer_threshold = float(self.customer_threshold.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number for Customer Spending Threshold.")
            return

        cursor.execute("""
            SELECT customer_name, total_spent
            FROM customer_spending_summary
            WHERE total_spent > ?
            ORDER BY total_spent DESC
        """, (customer_threshold,))
        rows = cursor.fetchall()

        if not rows:
            messagebox.showinfo("Top Customers", "No customers found above the threshold.")
            return

        report = f"Top Customers Report (Threshold: {customer_threshold}):\n"
        for row in rows:
            report += f"Customer: {row[0]}, Total Spent: {row[1]:.2f}\n"
        messagebox.showinfo("Top Customers", report)

    def view_order_summary_report(self):
        # Ask the user for the date of the order
        order_date = askstring("Input", "Enter the order date (YYYY-MM-DD):")
        if not order_date:
            messagebox.showerror("Input Error", "Please enter a valid order date.")
            return

        try:
            sales_threshold = float(self.sales_threshold.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number for Sales Threshold.")
            return

        # Use the reusable function to calculate total sales for the given date
        total_sales = self.calculate_total_sales_for_date(order_date)

        if total_sales <= sales_threshold:
            messagebox.showinfo("Order Summary Report", "No sales data above the threshold.")
            return

        report = f"Order Summary Report (Date: {order_date}, Threshold: {sales_threshold}):\n"
        report += f"Total Sales: {total_sales:.2f}\n"
        messagebox.showinfo("Order Summary Report", report)
