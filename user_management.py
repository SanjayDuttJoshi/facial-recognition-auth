import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
import os

class UserManagement:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("User Management")
        self.root.geometry("600x400")
        
        # Initialize database connection
        self.init_database()
        
        # Create GUI
        self.create_widgets()
        
    def init_database(self):
        """Initialize database connection"""
        try:
            self.conn = sqlite3.connect('face_auth.db')
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
            self.root.destroy()
            
    def create_widgets(self):
        """Create GUI widgets"""
        # Title
        title_label = tk.Label(self.root, text="User Management", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Create Treeview for user list
        self.tree = ttk.Treeview(self.root, columns=("ID", "Username"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Username", text="Username")
        self.tree.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        # Delete selected user button
        delete_btn = tk.Button(button_frame, text="Delete Selected User", 
                             command=self.delete_selected_user,
                             width=15, height=2)
        delete_btn.pack(side=tk.LEFT, padx=10)
        
        # Delete all users button
        delete_all_btn = tk.Button(button_frame, text="Delete All Users", 
                                 command=self.delete_all_users,
                                 width=15, height=2)
        delete_all_btn.pack(side=tk.LEFT, padx=10)
        
        # Refresh button
        refresh_btn = tk.Button(button_frame, text="Refresh List", 
                              command=self.refresh_user_list,
                              width=15, height=2)
        refresh_btn.pack(side=tk.LEFT, padx=10)
        
        # Load initial user list
        self.refresh_user_list()
        
    def refresh_user_list(self):
        """Refresh the user list in the Treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Fetch and display users
        try:
            self.cursor.execute("SELECT id, username FROM users")
            for user_id, username in self.cursor.fetchall():
                self.tree.insert("", "end", values=(user_id, username))
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load users: {str(e)}")
            
    def delete_selected_user(self):
        """Delete the selected user from the database"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
            
        user_id = self.tree.item(selected_item[0])['values'][0]
        username = self.tree.item(selected_item[0])['values'][1]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Deletion", 
                             f"Are you sure you want to delete user '{username}'?"):
            try:
                self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                self.conn.commit()
                messagebox.showinfo("Success", f"User '{username}' has been deleted")
                self.refresh_user_list()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to delete user: {str(e)}")
                
    def delete_all_users(self):
        """Delete all users from the database"""
        # Confirm deletion
        if messagebox.askyesno("Confirm Deletion", 
                             "Are you sure you want to delete ALL users?\nThis action cannot be undone!"):
            try:
                self.cursor.execute("DELETE FROM users")
                self.conn.commit()
                messagebox.showinfo("Success", "All users have been deleted")
                self.refresh_user_list()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to delete users: {str(e)}")
                
    def run(self):
        """Run the application"""
        self.root.mainloop()
        
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    app = UserManagement()
    try:
        app.run()
    finally:
        app.cleanup() 