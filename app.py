"""
ARND & Co AI Chatbot - Render.com Deployment
FREE Python Flask API with Firestore backend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import random
from datetime import datetime
import os
import re

# Initialize Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Firebase
import json
import sys

print("="*60)
print("Starting Firebase initialization...")
print("="*60)

# Load Firebase credentials from environment variable
firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')

if firebase_creds_json:
    print("✓ Environment variable found")
    try:
        # Parse JSON
        cred_dict = json.loads(firebase_creds_json)
        print(f"✓ JSON parsed successfully")
        print(f"✓ Project ID: {cred_dict.get('project_id', 'N/A')}")
        
        # Fix escaped newlines in private_key
        if 'private_key' in cred_dict and isinstance(cred_dict['private_key'], str):
            original_len = len(cred_dict['private_key'])
            # Replace escaped newlines with actual newlines
            cred_dict['private_key'] = cred_dict['private_key'].replace('\\\\n', '\n').replace('\\n', '\n')
            print(f"✓ Private key processed (length: {original_len} -> {len(cred_dict['private_key'])})")
        
        # Initialize Firebase
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        print("✅ Firebase initialized successfully!")
        print("="*60)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Environment variable content (first 100 chars): {firebase_creds_json[:100]}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        print(f"Error type: {type(e).__name__}")
        sys.exit(1)
else:
    print("❌ FIREBASE_CREDENTIALS_JSON environment variable not found!")
    print("Available environment variables:")
    for key in os.environ.keys():
        if 'FIREBASE' in key.upper():
            print(f"  - {key}")
    
    # Try local file as fallback
    print("\nTrying local serviceAccountKey.json...")
    try:
        cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase initialized from local file")
    except FileNotFoundError:
        print("❌ Local serviceAccountKey.json not found either!")
        print("Please set FIREBASE_CREDENTIALS_JSON environment variable in Render")
        sys.exit(1)

# ============================================================================
# VIRTUAL AGENTS CONFIG
# ============================================================================
AGENTS = {
    'Priya': {'emoji': '👩‍💼', 'gender': 'female', 'language': 'bengali'},
    'Ananya': {'emoji': '👩', 'gender': 'female', 'language': 'hindi'},
    'Arjun': {'emoji': '👨‍💼', 'gender': 'male', 'language': 'hindi'},
    'Rahul': {'emoji': '👨', 'gender': 'male', 'language': 'bengali'}
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def hash_password(password):
    """SHA-256 password hash"""
    return hashlib.sha256(password.encode()).hexdigest()

def select_agent(session_id):
    """Select virtual agent based on session_id (deterministic)"""
    agent_names = list(AGENTS.keys())
    hash_val = int(hashlib.md5(session_id.encode()).hexdigest()[:8], 16)
    index = hash_val % len(agent_names)
    name = agent_names[index]
    return {'name': name, **AGENTS[name]}

def detect_language(text):
    """Detect language: Bengali, Hindi, or English"""
    # Bengali Unicode
    if re.search(r'[\u0980-\u09FF]', text):
        return 'bengali'
    
    # Hindi/Devanagari Unicode
    if re.search(r'[\u0900-\u097F]', text):
        return 'hindi'
    
    # Romanized Bengali patterns
    bengali_patterns = r'\b(ami|tumi|apni|kemon|achen|korben|hobe|chai|dakha|banglai|ache|kore)\b'
    if re.search(bengali_patterns, text, re.IGNORECASE):
        return 'bengali'
    
    # Romanized Hindi patterns
    hindi_patterns = r'\b(mai|mujhe|aap|kaise|hain|karenge|hoga|chahiye|milega|hindi|kya)\b'
    if re.search(hindi_patterns, text, re.IGNORECASE):
        return 'hindi'
    
    return 'english'

def generate_response(message, context, agent, user_lang):
    """Generate AI chatbot response"""
    msg_lower = message.lower()
    
    # Product search
    if any(word in msg_lower for word in ['product', 'show', 'camera', 'lighting', 'fog', 'machine', 'buy']):
        products_ref = db.collection('products')
        products = products_ref.limit(5).stream()
        
        if agent['language'] == 'bengali':
            response = f"আমি {agent['name']} {agent['emoji']}। এই পণ্যগুলো দেখুন:\n\n"
        elif agent['language'] == 'hindi':
            response = f"मैं {agent['name']} {agent['emoji']} हूं। ये उत्पाद देखें:\n\n"
        else:
            response = f"I'm {agent['name']} {agent['emoji']}. Here are some products:\n\n"
        
        count = 0
        for product in products:
            p = product.to_dict()
            response += f"📦 {p.get('pname', 'Product')}\n"
            response += f"   💰 Price: ₹{p.get('price', 'N/A')}\n"
            if p.get('discounted_price') and float(p.get('discounted_price', 0)) < float(p.get('price', 0)):
                response += f"   🎉 Offer: ₹{p.get('discounted_price')}\n"
            response += "\n"
            count += 1
        
        if count == 0:
            return "Sorry, no products found. Please try again."
        return response
    
    # Brand inquiry
    if 'brand' in msg_lower or 'company' in msg_lower:
        brands_ref = db.collection('brands')
        brands = brands_ref.stream()
        
        if agent['language'] == 'bengali':
            response = "আমাদের ব্র্যান্ডগুলি:\n"
        elif agent['language'] == 'hindi':
            response = "हमारे ब्रांड:\n"
        else:
            response = "Our brands:\n"
        
        for brand in brands:
            b = brand.to_dict()
            response += f"✨ {b.get('name', 'Brand')}\n"
        
        return response
    
    # Greetings
    if re.search(r'\b(hi|hello|hey|namaste|namaskar)\b', msg_lower):
        if agent['language'] == 'bengali':
            return f"নমস্কার! আমি {agent['name']} {agent['emoji']}, ARND & Co এর ভার্চুয়াল সহায়ক। আমি আপনাকে কীভাবে সাহায্য করতে পারি?"
        elif agent['language'] == 'hindi':
            return f"नमस्ते! मैं {agent['name']} {agent['emoji']}, ARND & Co की वर्चुअल सहायक हूं। मैं आपकी कैसे मदद कर सकती हूं?"
        return f"Hello! I'm {agent['name']} {agent['emoji']}, your ARND & Co virtual assistant. How can I help you today?"
    
    # Price inquiry
    if 'price' in msg_lower or 'cost' in msg_lower or 'dam' in msg_lower or 'koto' in msg_lower:
        if agent['language'] == 'bengali':
            return f"দাম জানতে অনুগ্রহ করে নির্দিষ্ট পণ্যের নাম বলুন। আপনি 'show products' লিখতে পারেন সব পণ্য দেখার জন্য।"
        elif agent['language'] == 'hindi':
            return f"कीमत जानने के लिए कृपया उत्पाद का नाम बताएं। आप सभी उत्पाद देखने के लिए 'show products' लिख सकते हैं।"
        return f"Please specify which product you'd like to know the price of. Type 'show products' to see all products."
    
    # Default helpful response
    if agent['language'] == 'bengali':
        return f"{agent['name']} {agent['emoji']} এখানে! আমি আপনাকে পণ্য, দাম, এবং ব্র্যান্ড সম্পর্কে সাহায্য করতে পারি। আপনার প্রশ্ন কী?"
    elif agent['language'] == 'hindi':
        return f"{agent['name']} {agent['emoji']} यहाँ! मैं उत्पादों, कीमतों और ब्रांडों के बारे में आपकी मदद कर सकती हूं। आपका सवाल क्या है?"
    
    return f"{agent['name']} {agent['emoji']} here! I can help you with products, pricing, and brand information. What would you like to know?"

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/')
def home():
    return jsonify({
        'status': 'success',
        'message': 'ARND & Co Chatbot API is running',
        'version': '1.0.0',
        'endpoints': ['/health', '/signup', '/login', '/brands', '/chat_init', '/chat']
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'ARND & Co Chatbot API'
    })

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        mobile = data.get('mobile', '')
        password = data.get('password')
        
        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'Name, email and password are required'}), 400
        
        # Check if user exists
        users_ref = db.collection('chat_users')
        existing = users_ref.where('email', '==', email).limit(1).stream()
        
        if len(list(existing)) > 0:
            return jsonify({'success': False, 'message': 'Email already registered'}), 409
        
        # Create user
        user_data = {
            'name': name,
            'email': email,
            'mobile': mobile,
            'password_hash': hash_password(password),
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = users_ref.add(user_data)
        
        return jsonify({
            'success': True,
            'message': 'Signup successful',
            'user_id': doc_ref[1].id,
            'user': {'name': name, 'email': email}
        })
        
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'success': False, 'message': f'Signup failed: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        # Find user
        users_ref = db.collection('chat_users')
        users = users_ref.where('email', '==', email).limit(1).stream()
        
        user_list = list(users)
        if len(user_list) == 0:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        
        user_doc = user_list[0]
        user_data = user_doc.to_dict()
        password_hash = hash_password(password)
        
        if user_data.get('password_hash') != password_hash:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        
        # Update last login
        user_doc.reference.update({'last_login': firestore.SERVER_TIMESTAMP})
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user_id': user_doc.id,
            'user': {
                'name': user_data.get('name'),
                'email': user_data.get('email'),
                'mobile': user_data.get('mobile', '')
            }
        })
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': f'Login failed: {str(e)}'}), 500

@app.route('/brands', methods=['GET'])
def get_brands():
    try:
        brands_ref = db.collection('brands')
        brands = brands_ref.stream()
        
        brands_list = []
        for brand in brands:
            b = brand.to_dict()
            b['id'] = brand.id
            brands_list.append(b)
        
        return jsonify({'success': True, 'brands': brands_list})
        
    except Exception as e:
        print(f"Brands error: {e}")
        return jsonify({'success': False, 'message': f'Failed to fetch brands: {str(e)}'}), 500

@app.route('/chat_init', methods=['POST'])
def chat_init():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'user_id is required'}), 400
        
        # Generate session ID
        session_id = f"session_{int(datetime.utcnow().timestamp())}_{random.randint(1000, 9999)}"
        
        # Select virtual agent
        agent = select_agent(session_id)
        
        # Welcome message
        if agent['language'] == 'bengali':
            welcome = f"নমস্কার! আমি {agent['name']} {agent['emoji']}, আপনার ভার্চুয়াল সহায়ক। আমি আপনাকে পণ্য খুঁজতে এবং অর্ডার করতে সাহায্য করতে পারি। আপনার কী প্রয়োজন?"
        elif agent['language'] == 'hindi':
            welcome = f"नमस्ते! मैं {agent['name']} {agent['emoji']}, आपकी वर्चुअल सहायक हूं। मैं आपको उत्पाद खोजने और ऑर्डर करने में मदद कर सकती हूं। आपको क्या चाहिए?"
        else:
            welcome = f"Hello! I'm {agent['name']} {agent['emoji']}, your virtual shopping assistant. I can help you find products and place orders. What are you looking for?"
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'agent': agent,
            'welcome_message': welcome
        })
        
    except Exception as e:
        print(f"Chat init error: {e}")
        return jsonify({'success': False, 'message': f'Failed to initialize chat: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not user_id or not session_id or not message:
            return jsonify({'success': False, 'message': 'user_id, session_id and message are required'}), 400
        
        # Get agent for this session
        agent = select_agent(session_id)
        
        # Detect language
        user_lang = detect_language(message)
        
        # Generate response
        response = generate_response(message, {'user_id': user_id}, agent, user_lang)
        
        # Save to chat history
        db.collection('chat_history').add({
            'user_id': user_id,
            'session_id': session_id,
            'message': message,
            'response': response,
            'agent_name': agent['name'],
            'detected_language': user_lang,
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({
            'success': True,
            'response': response,
            'agent': agent,
            'detected_language': user_lang
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'success': False, 'message': f'Chat failed: {str(e)}'}), 500

# ============================================================================
# RUN
# ============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
