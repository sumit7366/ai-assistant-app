import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import random

app = Flask(__name__)

# ============================
# CONFIGURATION FOR RENDER
# ============================

# Secret Key
app.secret_key = 'y151a970b34b26af033dbd3365c94957320b566aa11ea985de2dfcedf1d511998' + os.urandom(24).hex()

# Render provides PORT environment variable
PORT = int(os.environ.get('PORT', 10000))

# File upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Use /tmp for uploads on Render (ephemeral storage)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'images', 'uploads')
DATA_FOLDER = os.path.join(os.getcwd(), 'data')

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# File paths
USERS_FILE = os.path.join(DATA_FOLDER, 'users.json')
IMAGES_FILE = os.path.join(DATA_FOLDER, 'images.json')
SUPPORT_FILE = os.path.join(DATA_FOLDER, 'support_requests.json')

# ============================
# HELPER FUNCTIONS
# ============================

def load_json(filepath):
    """Load JSON data from file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_json(filepath, data):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_files():
    """Initialize data files"""
    for file_path in [USERS_FILE, IMAGES_FILE, SUPPORT_FILE]:
        if not os.path.exists(file_path):
            save_json(file_path, {})

# Initialize files
init_files()

# ============================
# ROUTES (Your existing routes here)
# ============================
@app.after_request
def add_header(response):
    response.headers['Feature-Policy'] = "camera 'self'; microphone 'self'"
    response.headers['Permissions-Policy'] = "camera=(), microphone=()"
    return response

@app.route('/')
def index():
    """Home page"""
    if 'username' in session:
        return redirect(url_for('welcome'))
    return render_template('index.html')

@app.route('/save_name', methods=['POST'])
def save_name():
    """Save user's name"""
    name = request.form.get('name', '').strip()
    if name:
        session['username'] = name
        users = load_json(USERS_FILE)
        users[name] = {
            'first_seen': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat()
        }
        save_json(USERS_FILE, users)
    return redirect(url_for('welcome'))

@app.route('/welcome')
def welcome():
    """Welcome page"""
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('welcome.html', username=session['username'])

@app.route('/upload')
def upload():
    """Upload page"""
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/save_image', methods=['POST'])
def save_image():
    """Save uploaded image"""
    if 'username' not in session:
        return redirect(url_for('index'))
    
    username = session['username']
    
    if 'image' not in request.files:
        return redirect(url_for('upload'))
    
    file = request.files['image']
    description = request.form.get('description', '').strip()
    
    if file.filename == '':
        return redirect(url_for('upload'))
    
    if file and allowed_file(file.filename):
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{username}_{timestamp}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save file
            file.save(filepath)
            
            # Save metadata
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
            
            session['current_image_id'] = image_id
            return redirect(url_for('camera'))
            
        except Exception as e:
            print(f"Error: {e}")
            return redirect(url_for('upload'))
    
    return redirect(url_for('upload'))

@app.route('/camera')
def camera():
    """Camera page"""
    if 'username' not in session:
        return redirect(url_for('index'))
    
    description = ""
    image_id = session.get('current_image_id')
    if image_id:
        images = load_json(IMAGES_FILE)
        if image_id in images:
            description = images[image_id].get('description', '')
    
    return render_template('camera.html', description=description)

@app.route('/privacy')
def privacy():
    """Privacy page"""
    return render_template('privacy.html', current_year=datetime.now().year)

@app.route('/terms')
def terms():
    """Terms page"""
    return render_template('terms.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/support', methods=['GET', 'POST'])
def support():
    """Support page"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Save to file
        support_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'subject': subject,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        requests = load_json(SUPPORT_FILE)
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        requests[request_id] = support_data
        save_json(SUPPORT_FILE, requests)
        
        return render_template('support.html', success=True)
    
    return render_template('support.html', success=False)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Process camera frame"""
    if 'username' not in session:
        return jsonify({'success': False})
    
    try:
        # Get description
        description = ""
        image_id = session.get('current_image_id')
        if image_id:
            images = load_json(IMAGES_FILE)
            if image_id in images:
                description = images[image_id].get('description', '')
        
        # Simulate face detection
        face_detected = random.random() > 0.25
        
        return jsonify({
            'success': True,
            'face_detected': face_detected,
            'message': 'Face detected!' if face_detected else 'Looking for faces...',
            'description': description if face_detected else ''
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/close')
def close():
    """Close page"""
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('close.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'service': 'AI Assistant'})

# ============================
# MAIN FOR RENDER
# ============================

if __name__ == '__main__':
    print("🚀 Starting AI Assistant on Render...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Data folder: {DATA_FOLDER}")
    
    app.run(
        host='0.0.0.0',  # Required for Render
        port=PORT,        # Render provides PORT
        debug=False       # Debug OFF for production
    )
