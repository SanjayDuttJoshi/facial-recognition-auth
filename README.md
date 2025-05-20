# Face Recognition Authentication System

A secure facial recognition authentication system built with Python, using free and open-source libraries. This system provides a user-friendly GUI interface for registration and login using facial recognition technology.

## Features

- User registration with facial data capture
- Secure login using facial recognition
- Real-time face detection and tracking
- Lighting condition detection for optimal recognition
- User-friendly GUI interface
- Cross-platform compatibility (Windows and Ubuntu)
- Database management utilities

## Requirements

### For Ubuntu:
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y cmake
sudo apt-get install -y libopenblas-dev liblapack-dev
sudo apt-get install -y libx11-dev libgtk-3-dev
sudo apt-get install -y python3-tk
```

### For Windows:
1. Install Python 3.8 or later from [python.org](https://python.org)
2. Install Visual Studio Build Tools 2019 with C++ build tools
3. Install CMake from [cmake.org](https://cmake.org)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd face-recognition
```

2. Create and activate a virtual environment:

For Ubuntu:
```bash
python3 -m venv venv
source venv/bin/activate
```

For Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

1. Activate the virtual environment (if not already activated):
```bash
# Ubuntu
source venv/bin/activate

# Windows
.\venv\Scripts\activate
```

2. Run the application:
```bash
python app.py
```

### Database Management

The system uses SQLite database (`face_auth.db`) to store user information and face encodings. Several utilities are provided for database management:

1. View registered users:
```bash
python view_db.py
```

2. Database location:
- The database file (`face_auth.db`) is stored in the project root directory
- It contains user IDs, usernames, and face encodings
- The database is automatically created when the first user registers

3. User Management:
- Use the user management script to manage registered users:
```bash
python user_management.py
```
- Features:
  - View all registered users
  - Delete specific users
  - Manage user accounts
- The script provides an interactive interface for user management
- Changes are immediately reflected in the database

4. Database backup:
- It's recommended to regularly backup the `face_auth.db` file
- You can copy the file to a secure location for backup

## Troubleshooting

### Common Issues

1. **Camera Access Issues**
   - Ensure your camera is properly connected
   - Check if another application is using the camera
   - Verify camera permissions in your system settings

2. **Installation Problems**
   - Make sure all system dependencies are installed
   - Try reinstalling the virtual environment
   - Check Python version compatibility (3.8 or later)

3. **Recognition Issues**
   - Ensure good lighting conditions
   - Position your face properly in the frame
   - Try registering your face again if recognition fails

4. **Database Issues**
   - If the database becomes corrupted, delete `face_auth.db` and restart the application
   - Ensure the application has write permissions in the project directory

## Security Considerations

- Face data is stored locally in the SQLite database
- No data is transmitted over the network
- Regular backups of the database are recommended
- The system includes lighting condition detection for optimal recognition

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.