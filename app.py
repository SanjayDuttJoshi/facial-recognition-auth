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
import webbrowser
from flask import Flask, redirect, url_for
import subprocess
import sys
import dlib

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Create Flask app
flask_app = Flask(__name__)

# Always resolve the model path using resource_path
PREDICTOR_MODEL_REL = "face_recognition_models/models/shape_predictor_68_face_landmarks.dat"
predictor_path = resource_path(PREDICTOR_MODEL_REL)
if not os.path.exists(predictor_path):
    # Try relative to script as fallback
    predictor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), PREDICTOR_MODEL_REL)
    if not os.path.exists(predictor_path):
        tk.Tk().withdraw()  # Hide root window
        messagebox.showerror("Model Not Found", f"Could not find face predictor model at:\n{resource_path(PREDICTOR_MODEL_REL)}\nor\n{predictor_path}\n\nPlease ensure the model file is bundled correctly.")
        sys.exit(1)

# Load the dlib predictor ONCE, globally, for all uses
try:
    dlib_predictor = dlib.shape_predictor(predictor_path)
except Exception as e:
    tk.Tk().withdraw()
    messagebox.showerror("Model Load Error", f"Failed to load dlib model:\n{e}\nPath tried: {predictor_path}")
    sys.exit(1)

@flask_app.route('/logout')
def logout():
    # Restart the Python application
    python = sys.executable
    os.execl(python, python, *sys.argv)
    return "Logging out..."

def run_flask():
    flask_app.run(port=5000)

# Start Flask server in a separate thread
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

@flask_app.route('/')
def index():
    return "Face Authentication System"

class DashboardWindow:
    def __init__(self, parent, username):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Welcome {username}")
        self.window.geometry("400x300")
        
        # Center the window on screen
        self.center_window()
        
        # Create dashboard content
        self.create_widgets(username)
        
        # Auto redirect after 3 seconds
        self.redirect_timer = self.window.after(3000, self.redirect_to_localhost)
        
    def center_window(self):
        # Get screen width and height
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate position for center of the screen
        x = (screen_width - 400) // 2
        y = (screen_height - 300) // 2
        
        # Set the position of the window
        self.window.geometry(f"400x300+{x}+{y}")
        
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
            text="Login Successful!\nRedirecting to localhost:8080...",
            font=("Arial", 12),
            fg="green"
        )
        status_label.pack(pady=20)
        
        # Countdown label
        self.countdown_label = tk.Label(
            self.window,
            text="Redirecting in 3 seconds...",
            font=("Arial", 10),
            fg="blue"
        )
        self.countdown_label.pack(pady=10)
        
        # Start countdown
        self.countdown = 3
        self.update_countdown()
        
    def update_countdown(self):
        if self.countdown > 0:
            self.countdown_label.config(text=f"Redirecting in {self.countdown} seconds...")
            self.countdown -= 1
            self.window.after(1000, self.update_countdown)
        
    def redirect_to_localhost(self):
        try:
            # Open localhost:8080 in default browser
            webbrowser.open('http://localhost:8080')
            # Instead of iconify, just withdraw the window
            self.window.withdraw()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open browser: {str(e)}")

class FaceAuthSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Recognition Authentication")
        # Make window fullscreen (Linux compatible)
        self.root.attributes('-fullscreen', True)
        
        # Initialize database
        self.init_database()
        
        # Initialize camera
        self.camera = None
        self.is_camera_active = False
        
        # Enhanced camera performance settings
        self.camera_fps = 60  # Increased target FPS for smoother video
        self.frame_interval = int(1000 / self.camera_fps)  # Interval between frames in ms
        self.last_frame_time = 0
        self.frame_skip = 1  # Process every frame for smoother experience
        self.frame_count = 0
        self.target_resolution = (800, 600)  # Higher resolution for better quality
        
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
        
        # Timing parameters for 10-second delay
        self.camera_start_time = None
        self.recognition_delay = 4 # 4 seconds delay before recognition starts
        self.countdown_active = False
        
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
        # Welcome message
        welcome_label = tk.Label(self.main_frame, 
                               text="Welcome to the Bank Management System",
                               font=("Arial", 24, "bold"))
        welcome_label.pack(pady=40)
        
        # Title
        title_label = tk.Label(self.main_frame, 
                             text="Face Recognition Authentication", 
                             font=("Arial", 20, "bold"))
        title_label.pack(pady=20)
        
        # Buttons frame
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=40)
        
        # Register button
        register_btn = tk.Button(button_frame, 
                               text="Register", 
                               command=self.start_registration,
                               width=20, 
                               height=3,
                               font=("Arial", 12, "bold"))
        register_btn.pack(side=tk.LEFT, padx=20)
        
        # Login button
        login_btn = tk.Button(button_frame, 
                            text="Login", 
                            command=self.start_login,
                            width=20, 
                            height=3,
                            font=("Arial", 12, "bold"))
        login_btn.pack(side=tk.LEFT, padx=20)
        
        # Video frame
        self.video_frame = tk.Label(self.main_frame)
        self.video_frame.pack(pady=20)
        
        # Status label
        self.status_label = tk.Label(self.main_frame, text="", font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        # Countdown label for 10-second delay
        self.countdown_label = tk.Label(self.main_frame, text="", font=("Arial", 14), fg="blue")
        self.countdown_label.pack(pady=5)
        
        # Lighting status label
        self.lighting_label = tk.Label(self.main_frame, text="", font=("Arial", 12), fg="red")
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
    
    def check_face_already_registered(self, new_face_encoding):
        """Check if the face is already registered in the database"""
        if not self.known_face_encodings:
            return False, ""
    
        # Compare with all existing face encodings
        face_distances = face_recognition.face_distance(
            self.known_face_encodings,
        new_face_encoding
    )
        # Find the closest match
        min_distance = np.min(face_distances)
        closest_match_index = np.argmin(face_distances)
        
        # If the face is too similar to an existing one
        duplicate_threshold = 0.5  # Adjust this value as needed
        
        if min_distance < duplicate_threshold:
            existing_username = self.known_face_names[closest_match_index]
            return True, existing_username
        
        return False, ""
            
    def start_registration(self):
        """Start the registration process"""
        if self.is_camera_active:
            messagebox.showwarning("Warning", "Camera is already in use. Please wait.")
            return
            
        # Create a custom dialog for username input
        dialog = tk.Toplevel(self.root)
        dialog.title("Registration")
        dialog.geometry("400x200")
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Add padding
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack(expand=True, fill='both')
        
        # Username label
        label = tk.Label(frame, text="Enter username:", font=("Arial", 14))
        label.pack(pady=10)
        
        # Username entry
        username_var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=username_var, font=("Arial", 14), width=20)
        entry.pack(pady=10)
        
        # Submit button
        def submit():
            username = username_var.get().strip()
            if username:
                dialog.destroy()
                self.register_user(username)
            else:
                messagebox.showwarning("Warning", "Please enter a username")
        
        submit_btn = tk.Button(frame, text="Submit", command=submit, 
                             font=("Arial", 12), width=10, height=2)
        submit_btn.pack(pady=10)
        
        # Center the dialog on screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Set focus to entry
        entry.focus_set()
        
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
                
            # Set camera properties for better performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_resolution[1])
            self.camera.set(cv2.CAP_PROP_FPS, self.camera_fps)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for real-time processing
                
        self.is_camera_active = True
        self.camera_start_time = time.time()
        self.countdown_active = True
        
        # Start camera feed
        self.update_camera_feed()
        
    def update_camera_feed(self):
        """Update camera feed and handle face detection with improved performance"""
        if not self.is_camera_active:
            return
            
        # Calculate time since camera started
        if self.camera_start_time is not None:
            elapsed_time = time.time() - self.camera_start_time
            remaining_time = max(0, self.recognition_delay - elapsed_time)
            
            if remaining_time > 0 and self.countdown_active:
                self.countdown_label.config(text=f"Please wait... Recognition starts in {int(remaining_time + 1)} seconds")
                can_recognize = False
            else:
                self.countdown_label.config(text="")
                can_recognize = True
                self.countdown_active = False
        else:
            can_recognize = True
            
        ret, frame = self.camera.read()
        if not ret:
            self.status_label.config(text="Failed to capture frame. Please check camera connection.")
            self.root.after(10, self.update_camera_feed)
            return
            
        # Check lighting conditions
        lighting_ok, lighting_message = self.check_lighting_conditions(frame)
        if not lighting_ok:
            self.lighting_label.config(text=lighting_message)
            if can_recognize:
                self.status_label.config(text="Waiting for better lighting conditions...")
        else:
            self.lighting_label.config(text="")
            
        # Convert frame to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process face detection with improved performance
        self.frame_count += 1
        if self.frame_count % self.frame_skip == 0 and lighting_ok:
            # Detect faces with optimized settings
            face_locations = face_recognition.face_locations(rgb_frame, model="hog", number_of_times_to_upsample=1)
            
            if len(face_locations) == 0:
                if can_recognize:
                    self.status_label.config(text="No face detected. Please position your face in the camera view.")
            elif len(face_locations) > 1:
                if can_recognize:
                    self.status_label.config(text="Multiple faces detected. Please ensure only one face is visible.")
            else:
                # Draw rectangle around face
                top, right, bottom, left = face_locations[0]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Only process recognition after the delay
                if can_recognize:
                    # If in registration mode, capture face
                    if hasattr(self, 'current_username'):
                        if self.registration_count < self.registration_required:
                            face_encodings = face_recognition.face_encodings(rgb_frame, [face_locations[0]])
                            if face_encodings:
                                face_encoding = face_encodings[0]
                                self.registration_images.append(face_encoding)
                                self.registration_count += 1
                                
                                if self.registration_count < self.registration_required:
                                    self.status_label.config(text=f"Registration in progress... Capture {self.registration_count + 1}/{self.registration_required}")
                                else:
                                    self.complete_registration()
                                    return
                    # If in login mode, verify face
                    elif hasattr(self, 'login_mode'):
                        face_encodings = face_recognition.face_encodings(rgb_frame, [face_locations[0]])
                        if face_encodings:
                            face_encoding = face_encodings[0]
                            self.verify_face(face_encoding)
                            return
                else:
                    if hasattr(self, 'current_username'):
                        self.status_label.config(text=f"Get ready for registration... {int(remaining_time + 1)} seconds remaining")
                    elif hasattr(self, 'login_mode'):
                        self.status_label.config(text=f"Get ready for login... {int(remaining_time + 1)} seconds remaining")
                        
        # Convert frame to PhotoImage with better quality
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        # Resize image to fit the display area better
        display_size = (640, 480)
        image = image.resize(display_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image=image)
        
        # Update video frame
        self.video_frame.config(image=photo)
        self.video_frame.image = photo
        
        # Schedule next update with minimal delay for smoother video
        self.root.after(1, self.update_camera_feed)
        
    def complete_registration(self):
        """Complete the registration process"""
        # Stop camera and clear display first
        self.stop_camera_and_clear_display()
        
        if len(self.registration_images) == self.registration_required:
            # Calculate average face encoding
            avg_encoding = np.mean(self.registration_images, axis=0)

            # Check if this face is already registered
            is_duplicate, existing_username = self.check_face_already_registered(avg_encoding)
            if is_duplicate:
                messagebox.showerror("Error", f"This face is already registered with username: {existing_username}")
                self.status_label.config(text="Registration failed - Face already exists")
                # Cleanup
                if hasattr(self, 'current_username'):
                    delattr(self, 'current_username')
                return
            
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
        if hasattr(self, 'current_username'):
            delattr(self, 'current_username')
        
    def stop_camera_and_clear_display(self):
        """Stop camera and clear the video display"""
        self.is_camera_active = False
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        
        # Clear the video frame
        self.video_frame.config(image="")
        self.video_frame.image = None
        
        # Clear status labels
        self.countdown_label.config(text="")
        self.lighting_label.config(text="")
        
        # Reset timing variables
        self.camera_start_time = None
        self.countdown_active = False
        
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
                
            # Set camera properties for better performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_resolution[1])
            self.camera.set(cv2.CAP_PROP_FPS, self.camera_fps)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
        self.is_camera_active = True
        self.camera_start_time = time.time()
        self.countdown_active = True
        
        # Start camera feed
        self.update_camera_feed()
        
    def verify_face(self, face_encoding):
        """Verify face against known faces"""
        if not hasattr(self, 'login_mode'):
            return
            
        # Stop camera and clear display first
        self.stop_camera_and_clear_display()
        
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
            
            self.status_label.config(text=f"Face recognized as {username}")
            
            # Cleanup login mode
            if hasattr(self, 'login_mode'):
                delattr(self, 'login_mode')
            
            # Open dashboard (which will handle the redirect)
            DashboardWindow(self.root, username)
            
        else:
            self.login_attempts += 1
            if self.login_attempts >= self.max_login_attempts:
                messagebox.showerror("Error", "Maximum login attempts reached. Please try again later.")
                self.status_label.config(text="Login failed")
                
                # Cleanup
                if hasattr(self, 'login_mode'):
                    delattr(self, 'login_mode')
            else:
                self.status_label.config(text=f"Face not recognized. Attempt {self.login_attempts}/{self.max_login_attempts}")
                # Restart login process for another attempt
                self.start_login()
        
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