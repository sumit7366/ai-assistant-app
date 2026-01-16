import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import base64
from io import BytesIO

app = Flask(__name__)

# ============================
# PYTHONANYWHERE CONFIGURATION
# ============================

# Use absolute paths for PythonAnywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Secret Key - CHANGE THIS TO YOUR OWN RANDOM KEY!
app.secret_key = 'y151a970b34b26af033dbd3365c94957320b566aa11ea985de2dfcedf1d511998'

# ============================
# FILE UPLOAD CONFIGURATION
# ============================

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create absolute paths for PythonAnywhere
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'uploads')
DATA_FOLDER = os.path.join(BASE_DIR, 'data')

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

# Data files paths with absolute paths
USERS_FILE = os.path.join(DATA_FOLDER, 'users.json')
IMAGES_FILE = os.path.join(DATA_FOLDER, 'images.json')
SUPPORT_FILE = os.path.join(DATA_FOLDER, 'support_requests.json')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# ============================
# HELPER FUNCTIONS
# ============================

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

# ============================
# INITIALIZE DATA FILES
# ============================

# Initialize data files if they don't exist
for file_path in [USERS_FILE, IMAGES_FILE, SUPPORT_FILE]:
    if not os.path.exists(file_path):
        save_json(file_path, {})

# ============================
# CONTEXT PROCESSOR
# ============================

@app.context_processor
def inject_now():
    """Inject current datetime into all templates"""
    return {'now': datetime.now()}

# ============================
# ROUTES
# ============================

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
        return redirect(request.url)
    
    file = request.files['image']
    description = request.form.get('description', '').strip()
    
    if file.filename == '':
        return redirect(request.url)
    
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
        
        # Save support request to file
        support_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'subject': subject,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'ip_address': request.remote_addr
        }
        
        requests = load_json(SUPPORT_FILE)
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        requests[request_id] = support_data
        save_json(SUPPORT_FILE, requests)
        
        # Show success message
        return render_template('support.html', success=True)
    
    return render_template('support.html', success=False)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Process camera frame for face recognition (Simple version for PythonAnywhere)"""
    if 'username' not in session:
        return jsonify({'success': False})
    
    data = request.get_json()
    image_data = data.get('image', '')
    
    try:
        # Decode base64 image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Simple face detection simulation for PythonAnywhere
        # Since OpenCV might not work well on PythonAnywhere free tier
        
        # Get description from session
        description = ""
        image_id = session.get('current_image_id')
        if image_id:
            images = load_json(IMAGES_FILE)
            if image_id in images:
                description = images[image_id].get('description', '')
        
        # Simulate face detection (75% chance for demo)
        import random
        face_detected = random.random() > 0.25
        
        if face_detected:
            return jsonify({
                'success': True,
                'face_detected': True,
                'message': 'Face detected!',
                'description': description
            })
        else:
            return jsonify({
                'success': True,
                'face_detected': False,
                'message': 'Looking for faces...'
            })
            
    except Exception as e:
        print(f"Error processing frame: {e}")
        return jsonify({'success': False, 'error': str(e)})

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

@app.route('/health')
def health():
    """Health check endpoint for PythonAnywhere"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# ============================
# ERROR HANDLERS
# ============================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# ============================
# MAIN ENTRY POINT
# ============================

if __name__ == '__main__':
    # For local development only
    # On PythonAnywhere, this won't run (WSGI handles it)
    app.run(debug=True)