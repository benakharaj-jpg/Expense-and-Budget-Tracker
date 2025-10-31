import sqlite3
from datetime import datetime
import csv

# -----------------------------
# Database Setup
# -----------------------------
conn = sqlite3.connect("expense_tracker.db")
cursor = conn.cursor()

# Users table
cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE
)''')

# Expenses table
cursor.execute('''CREATE TABLE IF NOT EXISTS Expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    amount REAL,
    date TEXT,
    description TEXT,
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)''')

# Budgets table
cursor.execute('''CREATE TABLE IF NOT EXISTS Budgets (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    monthly_limit REAL,
    month TEXT,
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)''')

# Income table
cursor.execute('''CREATE TABLE IF NOT EXISTS Income (
    income_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    date TEXT,
    source TEXT,
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)''')

conn.commit()

# -----------------------------
# CRUD FUNCTIONS
# -----------------------------

# Users
def add_user():
    name = input("Enter Name: ")
    email = input("Enter Email: ")
    cursor.execute("INSERT INTO Users (name, email) VALUES (?, ?)", (name, email))
    conn.commit()
    print("✅ User added")

def view_users():
    cursor.execute("SELECT * FROM Users")
    for u in cursor.fetchall():
        print(u)

# Expenses
def add_expense():
    view_users()
    user_id = int(input("Enter User ID: "))
    category = input("Category (Food, Travel, Bills, etc.): ")
    amount = float(input("Amount: "))
    date = input("Date (YYYY-MM-DD) or leave blank for today: ")
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    description = input("Description: ")
    cursor.execute("INSERT INTO Expenses (user_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
                   (user_id, category, amount, date, description))
    conn.commit()
    print("✅ Expense added")
    check_budget(user_id, category, date[:7])

def view_expenses():
    cursor.execute('''SELECT e.expense_id, u.name, e.category, e.amount, e.date, e.description
                      FROM Expenses e
                      JOIN Users u ON e.user_id = u.user_id''')
    for e in cursor.fetchall():
        print(e)

def update_expense():
    view_expenses()
    expense_id = int(input("Enter Expense ID to update: "))
    category = input("New Category: ")
    amount = float(input("New Amount: "))
    date = input("New Date (YYYY-MM-DD): ")
    description = input("New Description: ")
    cursor.execute("UPDATE Expenses SET category=?, amount=?, date=?, description=? WHERE expense_id=?",
                   (category, amount, date, description, expense_id))
    conn.commit()
    print("✅ Expense updated")

def delete_expense():
    view_expenses()
    expense_id = int(input("Enter Expense ID to delete: "))
    cursor.execute("DELETE FROM Expenses WHERE expense_id=?", (expense_id,))
    conn.commit()
    print("✅ Expense deleted")

# Budgets
def add_budget():
    view_users()
    user_id = int(input("Enter User ID: "))
    category = input("Category: ")
    monthly_limit = float(input("Monthly Limit: "))
    month = input("Month (YYYY-MM): ")
    cursor.execute("INSERT INTO Budgets (user_id, category, monthly_limit, month) VALUES (?, ?, ?, ?)",
                   (user_id, category, monthly_limit, month))
    conn.commit()
    print("✅ Budget added")

def view_budgets():
    cursor.execute('''SELECT b.budget_id, u.name, b.category, b.monthly_limit, b.month
                      FROM Budgets b
                      JOIN Users u ON b.user_id = u.user_id''')
    for b in cursor.fetchall():
        print(b)

# Income
def add_income():
    view_users()
    user_id = int(input("Enter User ID: "))
    amount = float(input("Amount: "))
    date = input("Date (YYYY-MM-DD) or leave blank for today: ")
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    source = input("Source: ")
    cursor.execute("INSERT INTO Income (user_id, amount, date, source) VALUES (?, ?, ?, ?)",
                   (user_id, amount, date, source))
    conn.commit()
    print("✅ Income added")

# -----------------------------
# REPORTS & FUNCTIONS
# -----------------------------

def category_expense_report():
    view_users()
    user_id = int(input("Enter User ID: "))
    month = input("Enter Month (YYYY-MM): ")
    cursor.execute('''SELECT category, SUM(amount) FROM Expenses 
                      WHERE user_id=? AND substr(date,1,7)=? 
                      GROUP BY category''', (user_id, month))
    for r in cursor.fetchall():
        print(r)

def monthly_summary():
    view_users()
    user_id = int(input("Enter User ID: "))
    month = input("Enter Month (YYYY-MM): ")
    # Total Income
    cursor.execute('''SELECT SUM(amount) FROM Income WHERE user_id=? AND substr(date,1,7)=?''', (user_id, month))
    income = cursor.fetchone()[0] or 0
    # Total Expense
    cursor.execute('''SELECT SUM(amount) FROM Expenses WHERE user_id=? AND substr(date,1,7)=?''', (user_id, month))
    expense = cursor.fetchone()[0] or 0
    savings = income - expense
    print(f"Month: {month} | Income: {income} | Expenses: {expense} | Savings: {savings}")

def check_budget(user_id, category, month):
    cursor.execute('''SELECT monthly_limit FROM Budgets WHERE user_id=? AND category=? AND month=?''', 
                   (user_id, category, month))
    result = cursor.fetchone()
    if result:
        limit = result[0]
        cursor.execute('''SELECT SUM(amount) FROM Expenses WHERE user_id=? AND category=? AND substr(date,1,7)=?''',
                       (user_id, category, month))
        spent = cursor.fetchone()[0] or 0
        if spent > limit:
            print(f"⚠️ Alert! You exceeded budget for {category}. Limit: {limit}, Spent: {spent}")

def export_expenses_csv():
    view_users()
    user_id = int(input("Enter User ID to Export Expenses: "))
    cursor.execute("SELECT * FROM Expenses WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    filename = f"expenses_user_{user_id}.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Expense ID', 'User ID', 'Category', 'Amount', 'Date', 'Description'])
        writer.writerows(rows)
    print(f"✅ Expenses exported to {filename}")

def search_expenses():
    view_users()
    user_id = int(input("Enter User ID: "))
    category = input("Enter Category to Filter (leave blank for all): ")
    start_date = input("Start Date (YYYY-MM-DD, leave blank for all): ")
    end_date = input("End Date (YYYY-MM-DD, leave blank for all): ")
    
    query = "SELECT * FROM Expenses WHERE user_id=?"
    params = [user_id]
    
    if category:
        query += " AND category=?"
        params.append(category)
    if start_date:
        query += " AND date>=?"
        params.append(start_date)
    if end_date:
        query += " AND date<=?"
        params.append(end_date)
    
    cursor.execute(query, tuple(params))
    for e in cursor.fetchall():
        print(e)

# -----------------------------
# MENU
# -----------------------------
def menu():
    while True:
        print("\n--- Expense & Budget Tracker ---")
        print("1. Manage Users")
        print("2. Manage Expenses")
        print("3. Manage Budgets")
        print("4. Manage Income")
        print("5. Reports")
        print("6. Export Expenses to CSV")
        print("7. Search Expenses")
        print("8. Exit")
        choice = input("Enter Choice: ")

        if choice == "1":
            print("a. Add User\nb. View Users")
            sub = input("Choice: ")
            if sub == "a": add_user()
            elif sub == "b": view_users()
        elif choice == "2":
            print("a. Add Expense\nb. View Expenses\nc. Update Expense\nd. Delete Expense")
            sub = input("Choice: ")
            if sub == "a": add_expense()
            elif sub == "b": view_expenses()
            elif sub == "c": update_expense()
            elif sub == "d": delete_expense()
        elif choice == "3":
            print("a. Add Budget\nb. View Budgets")
            sub = input("Choice: ")
            if sub == "a": add_budget()
            elif sub == "b": view_budgets()
        elif choice == "4":
            add_income()
        elif choice == "5":
            print("a. Category-wise Expense\nb. Monthly Summary")
            sub = input("Choice: ")
            if sub == "a": category_expense_report()
            elif sub == "b": monthly_summary()
        elif choice == "6":
            export_expenses_csv()
        elif choice == "7":
            search_expenses()
        elif choice == "8":
            print("Exiting...")
            break
        else:
            print("❌ Invalid Choice")

# -----------------------------
# RUN SYSTEM
# -----------------------------
if __name__ == "__main__":
    menu()
