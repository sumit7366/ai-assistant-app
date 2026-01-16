import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import cv2
import numpy as np
from PIL import Image
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-123')

# Email Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'sumitranjanhisu@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'sumitranjanhisu@gmail.com')

mail = Mail(app)
# File upload configuration
UPLOAD_FOLDER = 'static/images/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# Data files paths
USERS_FILE = 'data/users.json'
IMAGES_FILE = 'data/images.json'
SUPPORT_FILE = 'data/support_requests.json'

def load_json(filepath):
    """Load JSON data from file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filepath, data):
    """Save data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize data files
if not os.path.exists(USERS_FILE):
    save_json(USERS_FILE, {})
if not os.path.exists(IMAGES_FILE):
    save_json(IMAGES_FILE, {})
if not os.path.exists(SUPPORT_FILE):
    save_json(SUPPORT_FILE, {})

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}


@app.route('/')
def index():
    """Home page with name input"""
    # Check if user already exists in session
    if 'username' in session:
        return redirect(url_for('welcome'))
    return render_template('index.html')

@app.route('/save_name', methods=['POST'])
def save_name():
    """Save user's name and create welcome session"""
    name = request.form.get('name', '').strip()
    if name:
        session['username'] = name
        
        # Save to persistent storage
        users = load_json(USERS_FILE)
        users[name] = {
            'first_seen': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat()
        }
        save_json(USERS_FILE, users)
        
    return redirect(url_for('welcome'))

@app.route('/welcome')
def welcome():
    """Welcome page after name entry"""
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('welcome.html', username=session['username'])

@app.route('/upload')
def upload():
    """Image upload page"""
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/save_image', methods=['POST'])
def save_image():
    """Save uploaded image and description"""
    if 'username' not in session:
        return redirect(url_for('index'))
    
    username = session['username']
    
    # Check if file was uploaded
    if 'image' not in request.files:
        return redirect(url_for('upload'))
    
    file = request.files['image']
    description = request.form.get('description', '').strip()
    
    if file.filename == '':
        return redirect(url_for('upload'))
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{username}_{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(filepath)
        
        # Save image info to database
        images = load_json(IMAGES_FILE)
        image_id = f"{username}_{timestamp}"
        
        images[image_id] = {
            'username': username,
            'filename': filename,
            'description': description,
            'uploaded_at': datetime.now().isoformat(),
            'filepath': filepath
        }
        save_json(IMAGES_FILE, images)
        
        # Store current image ID in session
        session['current_image_id'] = image_id
        
        return redirect(url_for('camera'))
    
    return redirect(url_for('upload'))

@app.route('/camera')
def camera():
    """Camera page for face recognition"""
    if 'username' not in session:
        return redirect(url_for('index'))
    
    # Get image description if available
    description = ""
    image_id = session.get('current_image_id')
    if image_id:
        images = load_json(IMAGES_FILE)
        if image_id in images:
            description = images[image_id].get('description', '')
    
    return render_template('camera.html', description=description)

# Add these routes after existing routes in app.py

@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    current_year = datetime.now().year
    return render_template('privacy.html', current_year=current_year)

@app.route('/terms')
def terms():
    """Terms and conditions page"""
    return render_template('terms.html')

@app.route('/support', methods=['GET', 'POST'])
def support():
    """Support contact page"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # In a real app, you would send an email here
        # For now, we'll save it to a JSON file
        support_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'subject': subject,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'ip_address': request.remote_addr
        }
        
        # Save support request to file
        support_file = 'data/support_requests.json'
        requests = load_json(support_file)
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        requests[request_id] = support_data
        save_json(support_file, requests)

        
        # Show success message
        return render_template('support.html', success=True)
    
    return render_template('support.html', success=False)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Process camera frame for face recognition"""
    if 'username' not in session:
        return jsonify({'success': False})
    
    data = request.get_json()
    image_data = data.get('image', '')
    
    # Decode base64 image
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    try:
        # Convert base64 to image
        img_data = base64.b64decode(image_data)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Simple face detection (in a real app, you'd use face_recognition library)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            return jsonify({
                'success': True,
                'face_detected': True,
                'message': 'Face detected!'
            })
        else:
            return jsonify({
                'success': True,
                'face_detected': False,
                'message': 'No face detected'
            })
            
    except Exception as e:
        print(f"Error processing frame: {e}")
        return jsonify({'success': False})

@app.route('/close')
def close():
    """Close agent page"""
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('close.html')

@app.route('/logout')
def logout():
    """Clear session and logout"""
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)