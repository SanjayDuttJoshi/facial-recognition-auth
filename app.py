import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog
import cv2
import numpy as np
import face_recognition
from PIL import Image, ImageTk
import threading
import time

class DashboardWindow:
    def __init__(self, parent, username):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Welcome {username}")
        self.window.geometry("400x300")
        
        # Center the window
        self.window.transient(parent)
        self.window.grab_set()
        
        # Create dashboard content
        self.create_widgets(username)
        
    def create_widgets(self, username):
        # Welcome message
        welcome_label = tk.Label(
            self.window,
            text=f"Welcome, {username}!",
            font=("Arial", 16, "bold")
        )
        welcome_label.pack(pady=20)
        
        # Status message
        status_label = tk.Label(
            self.window,
            text="You have successfully logged in.",
            font=("Arial", 10)
        )
        status_label.pack(pady=10)
        
        # Logout button
        logout_btn = tk.Button(
            self.window,
            text="Logout",
            command=self.logout,
            width=15,
            height=2
        )
        logout_btn.pack(pady=20)
        
    def logout(self):
        self.window.destroy()

class FaceAuthSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Recognition Authentication")
        self.root.geometry("800x600")
        
        # Initialize database
        self.init_database()
        
        # Initialize camera
        self.camera = None
        self.is_camera_active = False
        
        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Create buttons
        self.create_widgets()
        
        # Face recognition parameters
        self.known_face_encodings = []
        self.known_face_names = []
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.process_this_frame = True
        
        # Registration parameters
        self.registration_images = []
        self.registration_count = 0
        self.registration_required = 5
        
        # Login parameters
        self.login_attempts = 0
        self.max_login_attempts = 3
        self.recognition_threshold = 0.4  # Lower threshold for stricter matching
        
        # Lighting parameters
        self.low_light_threshold = 40  # Adjust this value based on testing
        self.consecutive_low_light_frames = 0
        self.max_low_light_frames = 10
        
        # Load known faces
        self.load_known_faces()
        
    def check_lighting_conditions(self, frame):
        """Check if the lighting conditions are adequate"""
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate average brightness
        brightness = np.mean(gray)
        
        if brightness < self.low_light_threshold:
            self.consecutive_low_light_frames += 1
            if self.consecutive_low_light_frames >= self.max_low_light_frames:
                return False, "Low light detected. Please improve lighting conditions."
        else:
            self.consecutive_low_light_frames = 0
            
        return True, ""
        
    def init_database(self):
        """Initialize SQLite database and create necessary tables"""
        try:
            self.conn = sqlite3.connect('face_auth.db')
            self.cursor = self.conn.cursor()
            
            # Create users table if it doesn't exist
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    face_encoding BLOB NOT NULL
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")
            self.root.destroy()
            
    def create_widgets(self):
        """Create GUI widgets"""
        # Title
        title_label = tk.Label(self.main_frame, text="Face Recognition Authentication", 
                             font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Buttons frame
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=20)
        
        # Register button
        register_btn = tk.Button(button_frame, text="Register", 
                               command=self.start_registration,
                               width=15, height=2)
        register_btn.pack(side=tk.LEFT, padx=10)
        
        # Login button
        login_btn = tk.Button(button_frame, text="Login", 
                            command=self.start_login,
                            width=15, height=2)
        login_btn.pack(side=tk.LEFT, padx=10)
        
        # Video frame
        self.video_frame = tk.Label(self.main_frame)
        self.video_frame.pack(pady=20)
        
        # Status label
        self.status_label = tk.Label(self.main_frame, text="", font=("Arial", 10))
        self.status_label.pack(pady=10)
        
        # Lighting status label
        self.lighting_label = tk.Label(self.main_frame, text="", font=("Arial", 10), fg="red")
        self.lighting_label.pack(pady=5)
        
    def load_known_faces(self):
        """Load known faces from database"""
        try:
            self.cursor.execute("SELECT username, face_encoding FROM users")
            for username, face_encoding in self.cursor.fetchall():
                self.known_face_names.append(username)
                self.known_face_encodings.append(np.frombuffer(face_encoding))
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load known faces: {str(e)}")
            
    def start_registration(self):
        """Start the registration process"""
        if self.is_camera_active:
            messagebox.showwarning("Warning", "Camera is already in use. Please wait.")
            return
            
        username = simpledialog.askstring("Registration", "Enter username:")
        if username:
            if self.check_username_exists(username):
                messagebox.showerror("Error", "Username already exists!")
                return
            self.register_user(username)
            
    def register_user(self, username):
        """Handle user registration process"""
        self.current_username = username
        self.registration_images = []
        self.registration_count = 0
        
        # Initialize camera if not already done
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                messagebox.showerror("Error", "Could not open camera! Please check if it's connected and not in use by another application.")
                return
                
        self.is_camera_active = True
        self.status_label.config(text=f"Registration in progress... Capture {self.registration_count + 1}/{self.registration_required}")
        
        # Start camera feed
        self.update_camera_feed()
        
    def update_camera_feed(self):
        """Update camera feed and handle face detection"""
        if not self.is_camera_active:
            return
            
        ret, frame = self.camera.read()
        if not ret:
            self.status_label.config(text="Failed to capture frame. Please check camera connection.")
            return
            
        # Check lighting conditions
        lighting_ok, lighting_message = self.check_lighting_conditions(frame)
        if not lighting_ok:
            self.lighting_label.config(text=lighting_message)
            self.status_label.config(text="Waiting for better lighting conditions...")
            # Schedule next update
            self.root.after(10, self.update_camera_feed)
            return
        else:
            self.lighting_label.config(text="")
            
        # Convert frame to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if len(face_locations) == 0:
            self.status_label.config(text="No face detected. Please position your face in the camera view.")
        elif len(face_locations) > 1:
            self.status_label.config(text="Multiple faces detected. Please ensure only one face is visible.")
        else:
            # Draw rectangle around face
            top, right, bottom, left = face_locations[0]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # If in registration mode, capture face
            if hasattr(self, 'current_username'):
                if self.registration_count < self.registration_required:
                    face_encoding = face_recognition.face_encodings(rgb_frame, [face_locations[0]])[0]
                    self.registration_images.append(face_encoding)
                    self.registration_count += 1
                    
                    if self.registration_count < self.registration_required:
                        self.status_label.config(text=f"Registration in progress... Capture {self.registration_count + 1}/{self.registration_required}")
                    else:
                        self.complete_registration()
            # If in login mode, verify face
            elif hasattr(self, 'login_mode'):
                face_encoding = face_recognition.face_encodings(rgb_frame, [face_locations[0]])[0]
                self.verify_face(face_encoding)
                        
        # Convert frame to PhotoImage
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)
        
        # Update video frame
        self.video_frame.config(image=photo)
        self.video_frame.image = photo
        
        # Schedule next update
        self.root.after(10, self.update_camera_feed)
        
    def complete_registration(self):
        """Complete the registration process"""
        if len(self.registration_images) == self.registration_required:
            # Calculate average face encoding
            avg_encoding = np.mean(self.registration_images, axis=0)
            
            # Verify the quality of the registration
            face_distances = []
            for encoding in self.registration_images:
                distance = face_recognition.face_distance([avg_encoding], encoding)[0]
                face_distances.append(distance)
            
            # Check if the registration samples are consistent
            if max(face_distances) > 0.3:  # If samples vary too much
                messagebox.showerror("Error", "Registration failed. Please try again with more consistent face positioning.")
                self.status_label.config(text="Registration failed - inconsistent samples")
                return
            
            try:
                # Save to database
                self.cursor.execute(
                    "INSERT INTO users (username, face_encoding) VALUES (?, ?)",
                    (self.current_username, avg_encoding.tobytes())
                )
                self.conn.commit()
                
                # Update known faces
                self.known_face_names.append(self.current_username)
                self.known_face_encodings.append(avg_encoding)
                
                messagebox.showinfo("Success", "Registration completed successfully!")
                self.status_label.config(text="Registration completed")
                
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to save registration: {str(e)}")
                
        # Cleanup
        self.is_camera_active = False
        self.camera.release()
        self.camera = None
        delattr(self, 'current_username')
        
    def start_login(self):
        """Start the login process"""
        if self.is_camera_active:
            messagebox.showwarning("Warning", "Camera is already in use. Please wait.")
            return
            
        if not self.known_face_names:
            messagebox.showinfo("Info", "No registered users found. Please register first.")
            return
            
        self.login_mode = True
        self.login_attempts = 0
        
        # Initialize camera if not already done
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                messagebox.showerror("Error", "Could not open camera! Please check if it's connected and not in use by another application.")
                return
                
        self.is_camera_active = True
        self.status_label.config(text="Login in progress... Please look at the camera")
        
        # Start camera feed
        self.update_camera_feed()
        
    def verify_face(self, face_encoding):
        """Verify face against known faces"""
        if not hasattr(self, 'login_mode'):
            return
            
        # Compare face with known faces
        face_distances = face_recognition.face_distance(
            self.known_face_encodings, 
            face_encoding
        )
        
        # Get the best match
        best_match_index = np.argmin(face_distances)
        best_match_distance = face_distances[best_match_index]
        
        # Check if the best match is within threshold
        if best_match_distance <= self.recognition_threshold:
            username = self.known_face_names[best_match_index]
            
            # Show success message
            messagebox.showinfo("Success", f"Welcome back, {username}!")
            self.status_label.config(text=f"Logged in as {username}")
            
            # Cleanup
            self.is_camera_active = False
            self.camera.release()
            self.camera = None
            delattr(self, 'login_mode')
            
            # Open dashboard
            DashboardWindow(self.root, username)
            
        else:
            self.login_attempts += 1
            if self.login_attempts >= self.max_login_attempts:
                messagebox.showerror("Error", "Maximum login attempts reached. Please try again later.")
                self.status_label.config(text="Login failed")
                
                # Cleanup
                self.is_camera_active = False
                self.camera.release()
                self.camera = None
                delattr(self, 'login_mode')
            else:
                self.status_label.config(text=f"Face not recognized. Attempt {self.login_attempts}/{self.max_login_attempts}")
        
    def check_username_exists(self, username):
        """Check if username already exists in database"""
        self.cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        return self.cursor.fetchone() is not None
        
    def run(self):
        """Start the application"""
        self.root.mainloop()
        
    def cleanup(self):
        """Cleanup resources"""
        if self.camera is not None:
            self.camera.release()
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    app = FaceAuthSystem()
    try:
        app.run()
    finally:
        app.cleanup() 