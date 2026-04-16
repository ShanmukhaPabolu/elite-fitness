from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
from flask_cors import CORS
import requests
import os
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient, errors
from werkzeug.security import generate_password_hash, check_password_hash
import json
from bson import ObjectId
import logging
from flask_mail import Mail, Message
import secrets
import string
import re
import google.generativeai as genai
from dotenv import load_dotenv
import webbrowser
import threading
import time

# Load environment variables from a .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Correctly configure the Flask app to find templates and static files ---
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_very_secret_key_that_is_not_secure')
CORS(app, supports_credentials=True)

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'rishik1074@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = ('Elite Performance', os.environ.get('MAIL_USERNAME', 'rishik1074@gmail.com'))

mail = Mail(app)

# Gemini AI API configuration
API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_GEMINI_API_KEY")
if not API_KEY:
    logger.error("GOOGLE_API_KEY not found. Please set the environment variable.")
else:
    genai.configure(api_key=API_KEY)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "fitness"

# Global variables for collections
client = None
db = None
users_collection = None
workout_logs = None
user_data_collection = None
sleep_logs = None

# Global flag to track if browser has been opened
browser_opened = False

def is_mongodb_connected():
    try:
        if client is None:
            return False
        client.admin.command('ping')
        return True
    except:
        return False

try:
    # Increase the timeout for the connection
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000, socketTimeoutMS=10000)
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB")
    
    db = client[DB_NAME]
    users_collection = db.users
    workout_logs = db.workout_logs
    user_data_collection = db.user_data
    sleep_logs = db.sleep_logs
    
    workout_logs.create_index([("user_email", 1), ("date", -1)])
    
    required_collections = ['users', 'workout_logs', 'user_data', 'sleep_logs', 'game_data', 'aura_data']
    existing_collections = db.list_collection_names()
    
    for coll in required_collections:
        if coll not in existing_collections:
            db.create_collection(coll)
            logger.info(f"Created collection: {coll}")
    
    logger.info("Database and collections initialized")
    
except errors.ServerSelectionTimeoutError as err:
    logger.error(f"MongoDB connection error: {err}")
    logger.warning("Running without MongoDB connection. Database operations will not work.")
except Exception as e:
    logger.error(f"Unexpected error initializing database: {e}")
    logger.warning("Running without MongoDB connection. Database operations will not work.")

# Register auth blueprint
from auth import auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/api/auth')

# Function to open browser after a delay (only once)
def open_browser():
    global browser_opened
    if not browser_opened:
        time.sleep(1.5)  # Wait for server to start
        webbrowser.open('http://127.0.0.1:5000')
        browser_opened = True

# =============================================================
# Frontend Page Routes
# =============================================================
@app.route('/')
def index_page():
    return send_from_directory(app.root_path, 'index.html')

@app.route('/login.html')
def login_page():
    return send_from_directory(app.root_path, 'login.html')

@app.route('/forgot_password.html')
def forgot_password_page():
    return send_from_directory(app.root_path, 'forgot_password.html')

@app.route('/goal.html')
def goal_page():
    return send_from_directory(app.root_path, 'goal.html')

@app.route('/ai-coach.html')
def ai_coach_page():
    return send_from_directory(app.root_path, 'ai-coach.html')

@app.route('/ai.html')
def ai_page():
    return send_from_directory(app.root_path, 'ai.html')

@app.route('/aivoice.html')
def aivoice_page():
    return send_from_directory(app.root_path, 'aivoice.html')

@app.route('/aura.html')
def aura_page():
    return send_from_directory(app.root_path, 'aura.html')
    
@app.route('/game.html')
def game_page():
    return send_from_directory(app.root_path, 'game.html')

@app.route('/leader.html')
def leader_page():
    return send_from_directory(app.root_path, 'leader.html')
    
@app.route('/login1.html')
def login1_page():
    return send_from_directory(app.root_path, 'login1.html')
    
@app.route('/plan.html')
def plan_page():
    return send_from_directory(app.root_path, 'plan.html')
    
@app.route('/sports.html')
def sports_page():
    return send_from_directory(app.root_path, 'sports.html')
    
@app.route('/stat.html')
def stat_page():
    return send_from_directory(app.root_path, 'stat.html')

@app.route('/workout.html')
def workout_page():
    return send_from_directory(app.root_path, 'workout.html')

@app.route('/lean.png')
def lean_image():
    return send_from_directory(app.root_path, 'lean.png')

@app.route('/overweight.png')
def overweight_image():
    return send_from_directory(app.root_path, 'overweight.png')

@app.route('/obese.png')
def obese_image():
    return send_from_directory(app.root_path, 'obese.png')

@app.route('/muscular.png') 
def muscular_image():
    return send_from_directory(app.root_path, 'muscular.png')
@app.route('/athletic.png')
def athletic_image():
    return send_from_directory(app.root_path, 'athletic.png')
@app.route('/stocky.png')
def stocky_image():
    return send_from_directory(app.root_path, 'stocky.png')

@app.route('/jj.png')
def jj_image():
    return send_from_directory(app.root_path, 'jj.png')

# Generic route to serve images and media from the root directory
@app.route('/<path:filename>')
def serve_root_assets(filename):
    # Only serve files with specific extensions from the root
    if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.webm', '.mp4', '.wav', '.mp3')):
        return send_from_directory(app.root_path, filename)
    # If not a recognized asset, let other routes handle it or return 404
    return "File not found", 404



# =============================================================
# Helper Functions for OTP
# =============================================================
def generate_otp(length=6):
    characters = string.digits
    return ''.join(secrets.choice(characters) for i in range(length))

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            logger.info(f"Email sent to {msg.recipients[0]}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

def send_otp_email(recipient_email, otp, subject, body):
    try:
        msg = Message(subject,
                      sender=app.config['MAIL_DEFAULT_SENDER'],
                      recipients=[recipient_email])
        msg.body = body
        thr = threading.Thread(target=send_async_email, args=[app, msg])
        thr.start()
        return True
    except Exception as e:
        logger.error(f"Failed to create email thread: {e}")
        return False

# =============================================================
# AI API Endpoint
# =============================================================

def format_dietary_restrictions(preferences, avoid_foods):
    """Format dietary restrictions for better AI understanding"""
    restrictions = []
    
    # Add dietary preferences
    if preferences:
        if len(preferences) == 1:
            restrictions.append(f"Diet type: {preferences[0]}")
        else:
            restrictions.append(f"Diet types: {', '.join(preferences)}")
    
    # Add foods to avoid
    if avoid_foods:
        if len(avoid_foods) <= 5:
            restrictions.append(f"Avoid: {', '.join(avoid_foods)}")
        else:
            # Group similar foods for better readability
            groups = {}
            for food in avoid_foods:
                category = food.split()[0] if food else "other"
                if category not in groups:
                    groups[category] = []
                groups[category].append(food)
            
            avoid_list = []
            for category, foods in groups.items():
                if len(foods) == 1:
                    avoid_list.append(foods[0])
                else:
                    avoid_list.append(f"{category} products ({len(foods)} types)")
            
            restrictions.append(f"Avoid: {', '.join(avoid_list)}")
    
    return ". ".join(restrictions) + "." if restrictions else "No specific dietary restrictions."

@app.route('/api/generate-plan', methods=['POST'])
def generate_plan():
    try:
        data = request.json or {}
        logger.debug(f"Frontend request payload: {data}")

        # Parse diet data if it's a JSON string
        diet_data = data.get('diet', 'balanced')
        if isinstance(diet_data, str):
            try:
                diet_data = json.loads(diet_data)
            except json.JSONDecodeError:
                diet_data = {"preferences": [], "avoidFoods": [], "hasHealthIssues": False, "healthConditions": []}
        
        # Extract dietary information
        dietary_preferences = diet_data.get('preferences', [])
        avoid_foods = diet_data.get('avoidFoods', [])
        has_health_issues = data.get('hasHealthIssues', False)
        health_conditions = data.get('healthConditions', [])
        
        logger.debug(f"Dietary preferences: {dietary_preferences}")
        logger.debug(f"Avoid foods: {avoid_foods}")
        logger.debug(f"Health issues: {has_health_issues}")
        logger.debug(f"Health conditions: {health_conditions}")
        
        # Format dietary restrictions for better AI understanding
        dietary_restrictions = format_dietary_restrictions(dietary_preferences, avoid_foods)
        
        # Build the prompt with user selections
        prompt = (
            "You are a fitness plan generator. Your ONLY output must be a single, valid JSON object. "
            "Do not include any text, explanation, or markdown formatting before or after the JSON. "
            "The JSON object must have three top-level keys: 'workout_plan', 'diet_plan', 'sleep_schedule'.\n"
            "- 'workout_plan' must be an array of objects with keys: 'd' (day), 't' (title), 'dur' (duration), 'ex' (array of exercises).\n"
            "- Each exercise object must have: 'n' (name), 's' (sets), 'r' (reps), 'desc' (description), 'icon' (string in 'fas fa-X' format).\n"
            "- 'diet_plan' must be an array of objects with: 'd' (day), 'mt' (meal type), 't' (title), 'det' (details).\n"
            "⚠️ Each meal must list specific foods (e.g., 'Oatmeal with banana', 'Paneer tikka with brown rice'). "
            "Do NOT use placeholders like 'Healthy Breakfast'.\n"
            "- 'sleep_schedule' must be an object with keys 'hrs' and 'rt'.\n"
            f"User details:\n"
            f"- Goal: {data.get('goal', 'general fitness')}\n"
            f"- Stats: {data.get('stats', 'N/A')}\n"
            f"- Body Type: {data.get('bodyType', 'average')}\n"
            f"- Level: {data.get('fitnessLevel', 'beginner')}\n"
            f"- Equipment & Mode: {data.get('equipment', 'minimal')}\n"
            f"- Dietary restrictions: {dietary_restrictions}\n"
            f"- Health considerations: {'Yes, ' + ', '.join(health_conditions) if health_conditions else 'None'}\n"
            f"- Age: {data.get('age', 25)}\n"
            f"- Weight: {data.get('weight', 70)} kg\n"
        )
        try:
            logger.debug("Creating Gemini model...")
            model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config={"response_mime_type": "application/json"}
            )
            logger.debug("Calling generate_content...")
            response = model.generate_content(prompt)
            logger.debug("Got response from Gemini API")

            response_text = response.text
            logger.debug(f"Response text: {response_text[:500]}")
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}", exc_info=True)
            
            # Check if it's a quota error (429)
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                logger.warning("Gemini API quota exceeded. Using fallback plan.")
                # Use fallback plan instead of failing
                response_text = None
            else:
                # For other errors, return error message
                raise

        # Clean markdown fences if present
        if isinstance(response_text, str):
            response_text = re.sub(r"^```(?:json)?", "", response_text.strip(), flags=re.MULTILINE)
            response_text = re.sub(r"```$", "", response_text.strip(), flags=re.MULTILINE)
        else:
            response_text = None

        # Try parsing JSON directly
        plan_data = {}
        if response_text:
            try:
                plan_data = json.loads(response_text)
                logger.debug(f"Successfully parsed JSON. Keys: {list(plan_data.keys())}")
            except json.JSONDecodeError:
                logger.warning("Direct JSON parse failed, trying regex extraction...")
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    clean_json_text = json_match.group(0)
                    try:
                        plan_data = json.loads(clean_json_text)
                        logger.debug(f"Successfully parsed JSON from regex. Keys: {list(plan_data.keys())}")
                    except Exception as e:
                        logger.error(f"Regex parse failed: {e}")
                        plan_data = {}
                else:
                    logger.warning("No JSON found in response")
                    plan_data = {}
        else:
            logger.warning("Response text is None")

        # Check what we have in the plan
        logger.debug(f"Plan data keys before fallback check: {list(plan_data.keys()) if plan_data else 'empty'}")
        logger.debug(f"Has workout_plan: {bool(plan_data.get('workout_plan'))}")
        logger.debug(f"Has diet_plan: {bool(plan_data.get('diet_plan'))}")
        logger.debug(f"Has sleep_schedule: {bool(plan_data.get('sleep_schedule'))}")

        # If still broken → fallback dummy
        if not plan_data.get("workout_plan") or not plan_data.get("diet_plan") or not plan_data.get("sleep_schedule"):
            logger.warning("AI response invalid or incomplete, falling back to dummy plan.")
            plan_data = {
                "workout_plan": [
                    {
                        "d": day,
                        "t": "Full Body Workout",
                        "dur": "60 min",
                        "ex": [
                            {"n": "Push-ups", "s": 4, "r": 15, "desc": "Standard push-ups", "icon": "fas fa-dumbbell"},
                            {"n": "Squats", "s": 4, "r": 20, "desc": "Bodyweight squats", "icon": "fas fa-dumbbell"},
                            {"n": "Plank", "s": 3, "r": "60 sec", "desc": "Core stability", "icon": "fas fa-dumbbell"}
                        ]
                    }
                    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                ],
                "diet_plan": [
                    meal
                    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    for meal in [
                        {
                            "d": day,
                            "mt": "Breakfast",
                            "t": "Morning Fuel",
                            "det": "Oatmeal with fresh fruits and a scoop of protein powder."
                        },
                        {
                            "d": day,
                            "mt": "Lunch",
                            "t": "Mid-day Recharge",
                            "det": "Grilled chicken breasts with quinoa and steamed broccoli."
                        },
                        {
                            "d": day,
                            "mt": "Snacks",
                            "t": "Evening Bite",
                            "det": "Greek yogurt with a handful of almonds and mixed berries."
                        },
                        {
                            "d": day,
                            "mt": "Dinner",
                            "t": "Night Recovery",
                            "det": "Baked salmon with sweet potato and a side of asparagus."
                        }
                    ]
                ],
                "sleep_schedule": {
                    "hrs": 8,
                    "rt": "Go to bed at 10 PM, wake up at 6 AM"
                }
            }
            logger.info("Fallback plan created with workout_plan, diet_plan, and sleep_schedule")
        else:
            logger.info("Complete plan structure received from AI")

        # Always include weight back in response
        plan_data["weight"] = data.get("weight", 70)

        return jsonify(plan_data)

    except Exception as e:
        logger.exception("Unexpected error in generate_plan")
        return jsonify({"message": f"Backend error: {str(e)}"}), 500

@app.route('/api/log-workout', methods=['POST'])
def log_workout():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "User not logged in"}), 401

    # Check if MongoDB is connected
    if not is_mongodb_connected():
        return jsonify({"success": False, "message": "Database not connected. Please try again later."}), 503

    try:
        data = request.json
        user_email = session.get('user_email')
        
        logger.debug(f"Received log workout request: {data}")
        
        # Create a complete workout entry with all plan details
        workout_entry = {
            "user_email": user_email,
            "date": datetime.now(timezone.utc),
            "goal": data.get("goal", ""),
            "age": data.get("age", ""),
            "weight": data.get("weight", ""),
            "height": data.get("height", {}),
            "fitnessLevel": data.get("fitnessLevel", ""),
            "bodyType": data.get("bodyType", ""),
            "equipment": data.get("equipment", []),
            "workoutMode": data.get("workoutMode", ""),
            "dietaryPreferences": data.get("dietaryPreferences", []),
            "avoidFoods": data.get("avoidFoods", []),
            "hasHealthIssues": data.get("hasHealthIssues", ""),
            "healthConditions": data.get("healthConditions", []),
            # Save the complete plan
            "plan": {
                "workout_plan": data.get("plan", {}).get("workout_plan", []),
                "diet_plan": data.get("plan", {}).get("diet_plan", []),
                "sleep_schedule": data.get("plan", {}).get("sleep_schedule", {}),
                "weight": data.get("weight", 70)
            }
        }
        
        logger.debug(f"Workout entry to save: {workout_entry}")
        
        # Insert into MongoDB
        result = workout_logs.insert_one(workout_entry)
        logger.debug(f"Inserted document with ID: {result.inserted_id}")
        
        return jsonify({
            "success": True, 
            "message": "Workout logged successfully.",
            "id": str(result.inserted_id)
        }), 200
    except Exception as e:
        logger.error(f"Error logging workout: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/get-workout-history', methods=['GET'])
def get_workout_history():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "User not logged in"}), 401

    # Check if MongoDB is connected
    if not is_mongodb_connected():
        return jsonify({"success": False, "message": "Database not connected. Please try again later."}), 503

    try:
        user_email = session.get('user_email')
        logger.debug(f"Fetching workout history for user: {user_email}")
        
        history = list(workout_logs.find({"user_email": user_email}).sort("date", -1))
        logger.debug(f"Found {len(history)} workout entries")

        # Convert ObjectId and datetime for JSON
        for entry in history:
            entry["_id"] = str(entry["_id"])
            entry["date"] = entry["date"].strftime("%Y-%m-%d %H:%M")
            
            # Ensure plan data is properly formatted
            if "plan" in entry:
                plan_data = entry["plan"]
                
                # If plan is stored as a string (which can happen with some MongoDB configurations)
                if isinstance(plan_data, str):
                    try:
                        plan_data = json.loads(plan_data)
                        entry["plan"] = plan_data
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse plan data for entry {entry['_id']}")
                        entry["plan"] = {
                            "workout_plan": [],
                            "diet_plan": [],
                            "sleep_schedule": {}
                        }
                
                # Ensure plan has required fields
                if not isinstance(plan_data, dict):
                    plan_data = {}
                    entry["plan"] = plan_data
                
                if "workout_plan" not in plan_data or not isinstance(plan_data["workout_plan"], list):
                    plan_data["workout_plan"] = []
                
                if "diet_plan" not in plan_data or not isinstance(plan_data["diet_plan"], list):
                    plan_data["diet_plan"] = []
                
                if "sleep_schedule" not in plan_data or not isinstance(plan_data["sleep_schedule"], dict):
                    plan_data["sleep_schedule"] = {}
                
                if "weight" not in plan_data:
                    plan_data["weight"] = entry.get("weight", 70)

        return jsonify(history), 200
    except Exception as e:
        logger.error(f"Error fetching workout history: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/test-mongo', methods=['GET'])
def test_mongo():
    try:
        # Test connection
        client.admin.command('ping')
        
        # Test collection
        test_doc = {"test": "value", "date": datetime.now(timezone.utc)}
        result = workout_logs.insert_one(test_doc)
        inserted_id = result.inserted_id
        
        # Retrieve the document
        retrieved_doc = workout_logs.find_one({"_id": inserted_id})
        
        # Delete the test document
        workout_logs.delete_one({"_id": inserted_id})
        
        return jsonify({
            "success": True,
            "message": "MongoDB connection test successful",
            "inserted_id": str(inserted_id),
            "retrieved_doc": {
                "test": retrieved_doc.get("test"),
                "date": retrieved_doc.get("date").isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"MongoDB test failed: {str(e)}"
        }), 500

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    logged_in = session.get('logged_in', False)
    user_email = session.get('user_email', None)
    user_name = session.get('user_name', None)  # Fetch the name from the session
    return jsonify({
        "logged_in": logged_in,
        "user_email": user_email,
        "user_name": user_name  # Return the user's name
    })


# =============================================================
# Chatbot Route
# =============================================================
@app.route('/api/askAI', methods=['POST'])
def ask_ai_chat():
    try:
        data = request.json or {}
        user_msg = data.get("message", "")
        language = data.get("language", "en-US")

        logger.debug(f"Chat request - Message: {user_msg}, Language: {language}")

        # Dictionary of intelligent prompts for different languages
        prompts = {
            "en": (
                "You are 'Elite AI Coach', a fitness expert assistant. "
                "Answer user questions about fitness, workouts, nutrition, training, and wellness. "
                "Rules: "
                "1. Be conversational and motivating. "
                "2. Keep answers concise (1-3 sentences). "
                "3. Provide practical, actionable advice. "
                "4. If asked about non-fitness topics, politely redirect to fitness topics. "
                "5. No markdown, plain text only."
            ),
            "hi": (
                "आप 'एलीट एआई कोच' हैं, एक फिटनेस विशेषज्ञ सहायक। "
                "फिटनेस, वर्कआउट, पोषण, प्रशिक्षण, और कल्याण के बारे में उपयोगकर्ता सवालों का जवाब दें। "
                "नियम: "
                "1. बातचीत और प्रेरक रहें। "
                "2. उत्तर संक्षिप्त रखें (1-3 वाक्य)। "
                "3. व्यावहारिक, कार्यान्वयन योग्य सलाह प्रदान करें। "
                "4. यदि गैर-फिटनेस विषयों के बारे में पूछा जाए, तो विनम्रतापूर्वक फिटनेस की ओर पुनः निर्देशित करें। "
                "5. कोई मार्कडाउन नहीं, केवल सादा पाठ।"
            )
        }
        
        lang_prefix = language.split('-')[0] if language else 'en'
        system_prompt = prompts.get(lang_prefix, prompts["en"])
        
        full_prompt = f"{system_prompt}\n\nUser: {user_msg}\nAssistant:"

        try:
            logger.debug(f"Calling Gemini API with prompt: {full_prompt[:100]}...")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(full_prompt)
            ai_reply = response.text.strip()
            logger.debug(f"Got Gemini response: {ai_reply[:100]}")
        except Exception as api_error:
            logger.error(f"Gemini API error: {str(api_error)}", exc_info=True)
            # Use intelligent fallback for ANY API error to remain useful to the user
            ai_reply = get_fallback_response(user_msg, lang_prefix)
        
        # Clean up formatting
        cleaned_reply = ai_reply.replace('**', '').replace('##', '').replace('*', '')
        cleaned_reply = re.sub(r'\[\[.*?\]\(https?:\/\/.*?\)\]', '', cleaned_reply)
        cleaned_reply = re.sub(r'\[\^\d+\]', '', cleaned_reply)
        
        # Remove lines with links
        lines = cleaned_reply.split('\n')
        cleaned_lines = [
            line for line in lines 
            if line.strip() and 'http' not in line and '.com' not in line and '.org' not in line
        ]
        cleaned_reply = ' '.join(cleaned_lines).strip()

        logger.debug(f"Final response: {cleaned_reply[:100]}")
        return jsonify({"success": True, "answer": cleaned_reply})

    except Exception as e:
        logger.exception("Unexpected error in ask_ai_chat")
        return jsonify({"success": False, "message": "I'm here to help! Please try your question again."}), 500


def get_fallback_response(user_msg, language="en"):
    """Generate context-aware fallback responses based on user message"""
    import random
    user_msg_lower = user_msg.lower()
    
    # Comprehensive fitness responses in English and Hindi
    responses_en = {
        # MUSCLE BUILDING
        "muscle|build|strength|gain|hypertrophy": [
            "Build muscle with a 5-day split: Mon: Chest/Triceps, Tue: Back/Biceps, Wed: Rest, Thu: Shoulders/Abs, Fri: Legs, Sat: Full Body/Sport, Sun: Rest. Focus on big lifts like squats, deadlifts, and bench press. Aim for 300-500 calorie surplus with 1.6-2g protein per kg.",
            "Elite 5-Day Hypertrophy Plan: Day 1: Upper Power, Day 2: Lower Power, Day 3: Rest, Day 4: Upper Hypertrophy, Day 5: Lower Hypertrophy, Day 6: Extra Mobility, Day 7: Rest. Consistency is king!",
            "For serious muscle gain, lift heavy in the 6-12 rep range. Prioritize compound movements and ensure you reach failure on your last sets. Eat every 3 hours and prioritize sleep (8+ hours) for hormone recovery.",
        ],
        "cardio|running|heart|endurance|aerobic|stamina": [
            "Elite 5-Day Endurance Plan: Day 1: 5km Steady Run, Day 2: HIIT Sprints (10x100m), Day 3: Rest, Day 4: Tempo Run (20 mins), Day 5: Long Slow Distance (10km+). Hydration is critical—drink 3L+ daily.",
            "Boost stamina with 150 mins of Zone 2 cardio weekly. On weekdays, do 20-min HIIT sessions. On weekends, focus on long-form activities like cycling or swimming for 60+ mins.",
        ],
        
        # WEIGHT LOSS & FAT
        "weight|lose|fat|slim|cut|deficit|calories": [
            "Lose weight via 300-500 calorie deficit. Combine strength training (preserves muscle) with 150+ mins cardio. Protein helps you stay full longer.",
            "Fat loss requires calorie deficit + consistency. Track your food, do resistance training 3x weekly, add cardio 3-4x weekly. Sleep and hydration matter!",
            "Weight loss basics: eat whole foods, protein at every meal, calorie deficit, strength training, and cardio. Aim for 0.5-1kg loss per week.",
        ],
        
        # DIET & NUTRITION
        "diet|nutrition|eat|food|protein|macro|carb|fat": [
            "Eat real foods: lean proteins (chicken, fish, eggs), complex carbs (oats, rice), healthy fats (nuts, olive oil), lots of veggies. Aim for 1.6-2.2g protein per kg.",
            "Nutrition basics: 40% protein, 40% carbs, 20% fats. Protein helps muscle recovery, carbs fuel workouts, fats support hormones. Drink 2-3L water daily!",
            "Smart nutrition: fill half your plate with vegetables, quarter protein, quarter carbs. Don't skip meals—eat every 3-4 hours for energy and recovery.",
        ],
        
        # ABS & CORE
        "abs|core|belly|six pack|pack|abdominal": [
            "Visible abs require low body fat (10-15%) + core training. Do planks, crunches, leg raises, and anti-rotation exercises 3x weekly. Diet determines visibility!",
            "Build core strength with compound lifts (squats, deadlifts) plus targeted work: planks (3x60s), cable crunches, hanging leg raises. Core strength improves posture.",
            "For abs: reduce body fat through diet and cardio, add core exercises. Strong core improves athletic performance and prevents back injuries too!",
        ],
        
        # RECOVERY & SLEEP
        "rest|recover|sleep|tired|fatigue|soreness": [
            "Recovery is when muscles grow! Get 7-9 hours quality sleep, stretch daily, foam roll sore muscles, take full rest day weekly. Nutrition aids recovery.",
            "Muscle soreness (DOMS) is normal after hard training. Ice, stretch, foam roll, and move gently. Full rest days let your body repair and get stronger.",
            "Prioritize sleep for recovery: 7-9 hours nightly improves strength, reduces injury risk, and boosts metabolism. Sleep is as important as workouts!",
        ],
        
        # BEGINNER
        "beginner|start|new|just|first time|noob": [
            "Welcome to fitness! Start with 3 workouts weekly, light weights or bodyweight. Focus on form over ego, be consistent, and celebrate small wins!",
            "Beginner tips: start with full-body workouts 3x weekly, learn proper form, don't compare yourself to others. Consistency > intensity. You've got this!",
            "Beginning your fitness journey? Pick one goal (muscle, weight loss, endurance), start simple, master form, then progressively increase difficulty.",
        ],
        
        # INJURY & PAIN
        "injury|pain|sore|hurt|ache|strain|sprain": [
            "Pain signals a problem—listen to your body! Rest, ice for 15 mins 2-3x daily, elevate. See a physical therapist if pain persists more than 3 days.",
            "Soreness after workouts is normal (DOMS), but shooting pain isn't. Modify exercises, reduce intensity, and get professional help if needed.",
            "Prevent injuries: warm up 5-10 mins, use proper form, don't skip rest days, stretch after workouts. Recovery prevents 80% of injuries!",
        ],
        
        # HYDRATION
        "hydration|water|drink|thirsty": [
            "Hydration is essential! Drink 2-3 liters daily, more during intense workouts. Proper hydration boosts performance, aids recovery, improves skin.",
            "Drink water consistently throughout the day. During workouts, aim for 400-800ml per hour depending on intensity. Electrolytes help during long sessions.",
            "Water supports every body function. Drink at least half your body weight (kg) in ml of water daily. Dehydration kills performance and recovery!",
        ],
        
        # WHO/HELP/INTRO
        "who are you|what do you do|help|assist": [
            "I'm your Elite AI Coach! I specialize in workouts, nutrition, recovery, and overall fitness. Ask me anything about your training goals!",
            "Hello! I'm Elite AI Coach, your fitness guide. I help with workout plans, nutrition advice, recovery strategies, and motivation. What's your goal?",
            "I'm here to help you achieve fitness success! Ask me about exercise techniques, meal planning, rest days, injuries—anything fitness-related!",
        ],
        
        # MOTIVATION
        "motivat|inspire|doubt|can't|discourag|fail": [
            "You've got this! Every expert was once a beginner. Stay consistent, trust the process, and celebrate progress over perfection. Keep going!",
            "Doubt is normal, but action beats doubt. One workout is better than zero. You're stronger than you think—keep pushing!",
            "Setbacks are setup for comebacks! Learn from failures, adjust your approach, and come back stronger. Progress isn't linear, but it's still progress!",
        ],
        
        # GENERAL/FALLBACK
        "default": [
            "That's an interesting question! Tell me more about your fitness goals. Are you building muscle, losing weight, improving endurance, or something else?",
            "Great question! I can help with workout routines, nutrition plans, recovery strategies, or motivation. What would you like to focus on?",
            "I'm here to support your fitness journey! Share your goal and I'll provide specific, actionable advice. What's on your mind?",
        ]
    }
    
    responses_hi = {
        # MUSCLE BUILDING
        "muscle|build|strength|gain|hypertrophy": [
            "मांसपेशियों का निर्माण करने के लिए 8-12 रेप्स करें, कंपाउंड मूव्स पर ध्यान दें: स्क्वाट्स, डेडलिफ्ट्स, बेंच प्रेस। हर हफ्ते वजन बढ़ाएं।",
            "मांसपेशियों की वृद्धि के लिए भारी प्रतिरोध प्रशिक्षण (6-12 रेप्स), पर्याप्त प्रोटीन (1.6-2.2g प्रति kg), और आराम चाहिए। प्रत्येक मांसपेशी को साप्ताहिक 2 बार ट्रेन करें।",
            "मांसपेशी लाभ के लिए: सप्ताह में 3-4 दिन भारी वजन उठाएं, अधिशेष में खाएं (300-500 कैलोरी), प्रोटीन को प्राथमिकता दें, और 7-9 घंटे सोएं।",
        ],
        
        # CARDIO & ENDURANCE
        "cardio|running|heart|endurance|aerobic|stamina": [
            "स्थिर दर कार्डियो (30-45 मिनट मध्यम तीव्रता) को HIIT (20-30 मिनट उच्च तीव्रता) के साथ मिलाएं। संतुलित फिटनेस के लिए शक्ति प्रशिक्षण जोड़ें।",
            "हृदय स्वास्थ्य के लिए बढ़िया! साप्ताहिक 150 मिनट मध्यम कार्डियो से शुरुआत करें। दौड़ना सहनशीलता बनाता है—5 मिनट वॉर्म-अप, दौड़ो, ठंडा करो।",
            "बेहतर सहनशीलता के लिए: साप्ताहिक एक बार लंबी दौड़, मध्य सप्ताह में तेज दौड़, और HIIT स्प्रिंट। रिकवरी दिन महत्वपूर्ण हैं!",
        ],
        
        # WEIGHT LOSS & FAT
        "weight|lose|fat|slim|cut|deficit|calories": [
            "वजन कम करने के लिए 300-500 कैलोरी की कमी बनाएं। शक्ति प्रशिक्षण (मांसपेशी सुरक्षित करता है) के साथ 150+ मिनट कार्डियो को मिलाएं।",
            "वसा हानि की आवश्यकता है कैलोरी कमी + निष्ठा। अपने भोजन को ट्रैक करें, साप्ताहिक 3 दिन प्रतिरोध प्रशिक्षण, 3-4 दिन कार्डियो। नींद और हाइड्रेशन महत्वपूर्ण हैं!",
            "वजन घटाने की मूल बातें: पूरे भोजन खाएं, प्रत्येक भोजन में प्रोटीन, कैलोरी कमी, शक्ति प्रशिक्षण, और कार्डियो। साप्ताहिक 0.5-1kg नुकसान का लक्ष्य रखें।",
        ],
        
        # DIET & NUTRITION
        "diet|nutrition|eat|food|protein|macro|carb|fat": [
            "असली भोजन खाएं: लीन प्रोटीन (चिकन, मछली, अंडे), जटिल कार्ब्स (ओट्स, चावल), स्वस्थ वसा (नट्स, जैतून का तेल), बहुत सब्जियां। प्रति kg 1.6-2.2g प्रोटीन लक्ष्य करें।",
            "पोषण मूलभूत: 40% प्रोटीन, 40% कार्ब्स, 20% वसा। प्रोटीन मांसपेशी पुनरावृत्ति में मदद करता है, कार्ब्स वर्कआउट को ईंधन देते हैं, वसा हार्मोन का समर्थन करती है।",
            "स्मार्ट पोषण: अपनी आधी प्लेट सब्जियों से भरें, एक चौथाई प्रोटीन, एक चौथाई कार्ब्स। भोजन न छोड़ें—ऊर्जा और रिकवरी के लिए हर 3-4 घंटे खाएं।",
        ],
        
        # ABS & CORE
        "abs|core|belly|six pack|pack|abdominal": [
            "दृश्यमान पेट की मांसपेशियों के लिए कम शरीर वसा (10-15%) + कोर प्रशिक्षण चाहिए। प्लैंक्स, क्रंचेस, लेग राइज़, एंटी-रोटेशन व्यायाम साप्ताहिक 3 बार करें।",
            "कंपाउंड लिफ्ट्स (स्क्वाट्स, डेडलिफ्ट्स) के साथ कोर शक्ति बनाएं, फिर लक्षित काम: प्लैंक्स, केबल क्रंचेस, हैंगिंग लेग राइज़। मुद्रा में सुधार करता है।",
            "पेट की मांसपेशियों के लिए: भोजन और कार्डियो के माध्यम से शरीर की वसा कम करें, कोर व्यायाम जोड़ें। मजबूत कोर एथलेटिक प्रदर्शन में सुधार करता है!",
        ],
        
        # RECOVERY & SLEEP
        "rest|recover|sleep|tired|fatigue|soreness": [
            "रिकवरी तब होती है जब मांसपेशियां बढ़ती हैं! 7-9 घंटे की गुणवत्ता नींद लें, रोज स्ट्रेच करें, फोम रोल करें, साप्ताहिक एक आराम दिन लें।",
            "मांसपेशियों की पीड़ा (DOMS) कठोर प्रशिक्षण के बाद सामान्य है। आइस लगाएं, स्ट्रेच करें, फोम रोल करें, हल्के आंदोलन करें। रिकवरी बॉडी को मजबूत बनाता है।",
            "नींद को प्राथमिकता दें रिकवरी के लिए: रात को 7-9 घंटे शक्ति बढ़ाता है, चोट का जोखिम कम करता है, और चयापचय बढ़ाता है। नींद वर्कआउट जितनी महत्वपूर्ण है!",
        ],
        
        # BEGINNER
        "beginner|start|new|just|first time|noob": [
            "फिटनेस में स्वागत है! साप्ताहिक 3 वर्कआउट से शुरुआत करें, हल्के वजन या बॉडीवेट। फॉर्म पर ध्यान दें, निरंतर रहें, और छोटी जीत का जश्न मनाएं!",
            "नौसिखिए सुझाव: साप्ताहिक 3 बार पूरे शरीर के वर्कआउट, सही फॉर्म सीखें, अपने आप को दूसरों से न तुलना करें। निरंतरता > तीव्रता।",
            "फिटनेस यात्रा शुरू करें? एक लक्ष्य चुनें (मांसपेशी, वजन घटाना, सहनशीलता), सरल शुरुआत करें, फॉर्म में महारत हासिल करें, फिर धीरे-धीरे कठिनाई बढ़ाएं।",
        ],
        
        # INJURY & PAIN
        "injury|pain|sore|hurt|ache|strain|sprain": [
            "दर्द एक संकेत है—अपने शरीर को सुनें! आराम करें, 15 मिनट के लिए आइस लगाएं 2-3 बार। यदि दर्द 3 दिन से अधिक रहे तो फिजियोथेरेपिस्ट से मिलें।",
            "वर्कआउट के बाद मांसपेशियों की पीड़ा सामान्य है (DOMS), लेकिन तीव्र दर्द नहीं। व्यायाम को संशोधित करें, तीव्रता कम करें, और पेशेवर मदद लें।",
            "चोटों को रोकें: 5-10 मिनट वॉर्म-अप, सही फॉर्म, आराम दिन न छोड़ें, वर्कआउट के बाद स्ट्रेच करें। रिकवरी 80% चोटों को रोकता है!",
        ],
        
        # HYDRATION
        "hydration|water|drink|thirsty": [
            "हाइड्रेशन आवश्यक है! दैनिक 2-3 लीटर पिएं, तीव्र वर्कआउट के दौरान अधिक। उचित हाइड्रेशन प्रदर्शन बढ़ाता है, रिकवरी में मदद करता है।",
            "पूरे दिन लगातार पानी पिएं। वर्कआउट के दौरान, तीव्रता के आधार पर प्रति घंटे 400-800ml का लक्ष्य रखें। इलेक्ट्रोलाइट्स लंबे सत्रों में मदद करता है।",
            "पानी शरीर के हर कार्य का समर्थन करता है। अपने शरीर के वजन (kg) के आधे का ml पानी दैनिक पिएं। निर्जलीकरण प्रदर्शन को मारता है!",
        ],
        
        # WHO/HELP/INTRO
        "who are you|what do you do|help|assist": [
            "मैं आपका एलीट एआई कोच हूँ! मैं वर्कआउट, पोषण, रिकवरी, और फिटनेस में विशेषज्ञ हूँ। अपने प्रशिक्षण लक्ष्यों के बारे में कुछ भी पूछें!",
            "नमस्ते! मैं एलीट एआई कोच हूँ, आपका फिटनेस गाइड। मैं वर्कआउट योजनाओं, पोषण सलाह, रिकवरी रणनीतियों में मदद करता हूँ। आपका लक्ष्य क्या है?",
            "मैं आपकी फिटनेस सफलता में मदद करने के लिए यहाँ हूँ! व्यायाम तकनीक, भोजन योजना, आराम दिनों के बारे में पूछें—कुछ भी फिटनेस-संबंधी!",
        ],
        
        # MOTIVATION
        "motivat|inspire|doubt|can't|discourag|fail": [
            "तुम यह कर सकते हो! हर विशेषज्ञ एक शुरुआत था। निरंतर रहें, प्रक्रिया पर विश्वास करें, और प्रगति का जश्न मनाएं। आगे बढ़ो!",
            "संदेह सामान्य है, लेकिन कार्य संदेह को हराता है। एक वर्कआउट कोई वर्कआउट नहीं से बेहतर है। तुम सोचते हो से अधिक मजबूत हो!",
            "असफलताएं वापसी के लिए सेटअप हैं! विफलताओं से सीखें, अपने दृष्टिकोण को समायोजित करें, और अधिक मजबूत वापस आएं। प्रगति रैखिक नहीं है, लेकिन अभी भी प्रगति है!",
        ],
        
        # GENERAL/FALLBACK
        "default": [
            "यह एक दिलचस्प सवाल है! अपने फिटनेस लक्ष्यों के बारे में अधिक बताएं। क्या आप मांसपेशी बनाना चाहते हैं, वजन कम करना चाहते हैं, या सहनशीलता में सुधार करना चाहते हैं?",
            "बढ़िया सवाल! मैं वर्कआउट रूटीन, पोषण योजनाओं, रिकवरी रणनीतियों, या प्रेरणा में मदद कर सकता हूँ। आप किस पर ध्यान केंद्रित करना चाहते हैं?",
            "मैं आपकी फिटनेस यात्रा का समर्थन करने के लिए यहाँ हूँ! अपना लक्ष्य साझा करें और मैं विशिष्ट, कार्यान्वयन योग्य सलाह दूंगा।",
        ]
    }
    
    # Select response based on language
    responses = responses_hi if language == "hi" else responses_en
    
    # Find matching category
    selected_responses = None
    for pattern, response_list in responses.items():
        if pattern != "default":
            keywords = pattern.split('|')
            if any(keyword in user_msg_lower for keyword in keywords):
                selected_responses = response_list
                break
    
    # Use default if no match
    if not selected_responses:
        selected_responses = responses["default"]
    
    # Return random response from the category
    chosen_response = random.choice(selected_responses)
    logger.debug(f"Using fallback {language} response for: {user_msg[:50]} -> {chosen_response[:100]}")
    return chosen_response

# =============================================================
# Login, Registration & OTP Flow
# =============================================================
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({"success": False, "message": "Please provide name, email, and password."}), 400
        
    if not is_mongodb_connected():
        return jsonify({"success": False, "message": "Database not connected. Please try again later."}), 503
        
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        return jsonify({"success": False, "message": "Email is already registered."}), 400
        
    hashed_password = generate_password_hash(password)
    users_collection.insert_one({
        "name": name,
        "email": email,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "auth_provider": "local"
    })
    
    return jsonify({"success": True, "message": "Registration successful."}), 201

@app.route('/api/login', methods=['POST'])
def login():
    # Clear any previous OTP session data
    session.pop('otp', None)
    session.pop('otp_timestamp', None)
    session.pop('resend_count', None)

    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = users_collection.find_one({"email": email})
    if user and check_password_hash(user['password'], password):
        otp = generate_otp()
        subject = "OTP for Elite Performance Login"
        body = f"OTP For Login is: {otp} VALID FOR 5 MINUTES"
        if send_otp_email(email, otp, subject, body):
            session['otp'] = otp
            session['otp_timestamp'] = datetime.now(timezone.utc)
            session['temp_user_email'] = email
            session['resend_count'] = 0
            return jsonify({"success": True, "message": "OTP sent to your email."}), 200
        else:
            return jsonify({"success": False, "message": "Failed to send OTP. Please try again."}), 500
    else:
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

@app.route('/api/verify-login-otp', methods=['POST'])
def verify_login_otp():
    data = request.json
    otp = data.get('otp')
    
    stored_otp = session.get('otp')
    otp_timestamp = session.get('otp_timestamp')
    
    if not stored_otp or not otp_timestamp:
        return jsonify({"success": False, "message": "OTP not found or expired. Please try again."}), 400
        
    if datetime.now(timezone.utc) - otp_timestamp > timedelta(minutes=5):
        session.pop('otp', None)
        session.pop('otp_timestamp', None)
        session.pop('resend_count', None)
        return jsonify({"success": False, "message": "OTP has expired. Please try again."}), 400
        
    if otp == stored_otp:
        user_email = session.get('temp_user_email')
        user = users_collection.find_one({"email": user_email})
        
        for key in ['otp', 'otp_timestamp', 'temp_user_email', 'resend_count']:
            session.pop(key, None)
        
        session['logged_in'] = True
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        return jsonify({"success": True, "name": user['name'], "message": "Login successful."}), 200
    else:
        return jsonify({"success": False, "message": "Invalid OTP."}), 401

# =============================================================
# Forgot Password Flow
# =============================================================
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    # Clear any previous OTP session data
    session.pop('otp', None)
    session.pop('otp_timestamp', None)
    session.pop('resend_count', None)
    
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400

    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "Username not found."}), 404

    otp = generate_otp()
    subject = "OTP for Elite Performance Password Reset"
    body = f"OTP For Resetting The Password is: {otp} VALID FOR 5 MINUTES"
    if send_otp_email(email, otp, subject, body):
        session['otp'] = otp
        session['otp_timestamp'] = datetime.now(timezone.utc)
        session['reset_email'] = email
        session['resend_count'] = 0
        return jsonify({"success": True, "message": "OTP sent to your email."}), 200
    else:
        return jsonify({"success": False, "message": "Failed to send OTP. Please try again."}), 500

@app.route('/api/verify-forgot-password-otp', methods=['POST'])
def verify_forgot_password_otp():
    data = request.json
    otp = data.get('otp')
    new_password = data.get('new_password')

    stored_otp = session.get('otp')
    otp_timestamp = session.get('otp_timestamp')
    email = session.get('reset_email')
    
    if not stored_otp or not otp_timestamp or not email:
        return jsonify({"success": False, "message": "OTP not found or expired. Please try again."}), 400
        
    if datetime.now(timezone.utc) - otp_timestamp > timedelta(minutes=5):
        for key in ['otp', 'otp_timestamp', 'reset_email', 'resend_count']:
            session.pop(key, None)
        return jsonify({"success": False, "message": "OTP has expired. Please try again."}), 400
        
    if otp == stored_otp:
        for key in ['otp', 'otp_timestamp', 'reset_email', 'resend_count']:
            session.pop(key, None)
        
        new_hashed_password = generate_password_hash(new_password)
        users_collection.update_one({"email": email}, {"$set": {"password": new_hashed_password}})
        return jsonify({"success": True, "message": "Password updated successfully."}), 200
    else:
        return jsonify({"success": False, "message": "Invalid OTP."}), 401

# =============================================================
# Resend OTP Endpoint
# =============================================================
@app.route('/api/resend-otp', methods=['POST'])
def resend_otp():
    otp_timestamp = session.get('otp_timestamp')
    user_email = session.get('temp_user_email') or session.get('reset_email')

    if not otp_timestamp or not user_email:
        return jsonify({"success": False, "message": "No active OTP session. Please start over."}), 400
    
    # Determine the context of the OTP request
    is_login_flow = 'temp_user_email' in session
    subject = "OTP for Elite Performance Login" if is_login_flow else "OTP for Elite Performance Password Reset"

    is_expired = (datetime.now(timezone.utc) - otp_timestamp) > timedelta(minutes=5)

    if is_expired:
        new_otp = generate_otp()
        body = f"Your OTP is: {new_otp}"
        if send_otp_email(user_email, new_otp, subject, body):
            session['otp'] = new_otp
            session['otp_timestamp'] = datetime.now(timezone.utc)
            session['resend_count'] = 0
            return jsonify({"success": True, "message": "Your previous OTP expired. A new one has been sent."})
        else:
            return jsonify({"success": False, "message": "Failed to send a new OTP. Please try again."}), 500
    else:
        resend_count = session.get('resend_count', 0)
        if resend_count >= 3:
            return jsonify({"success": False, "message": "Max resend attempts reached. Please wait 5 minutes for a new OTP."}), 429
        
        current_otp = session.get('otp')
        body = f"Your OTP is: {current_otp}"
        if send_otp_email(user_email, current_otp, subject, body):
            session['resend_count'] = resend_count + 1
            remaining = 3 - session['resend_count']
            return jsonify({"success": True, "message": f"OTP has been resent. You have {remaining} attempts remaining."})
        else:
            return jsonify({"success": False, "message": "Failed to resend OTP. Please try again."}), 500

# =============================================================
# Reset Password (Logged-in Users)
# =============================================================
@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "User not logged in"}), 401
    
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    user_email = session.get('user_email')
    
    user = users_collection.find_one({"email": user_email})
    if user and check_password_hash(user['password'], old_password):
        new_hashed_password = generate_password_hash(new_password)
        users_collection.update_one({"email": user_email}, {"$set": {"password": new_hashed_password}})
        return jsonify({"success": True, "message": "Password updated successfully."}), 200
    else:
        return jsonify({"success": False, "message": "Incorrect old password."}), 401

@app.route('/api/log', methods=['POST'])
def log_plan():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "User not logged in"}), 401

    data = request.json or {}
    log_entry = {
        "user_email": session.get("user_email"),
        "date": datetime.now(timezone.utc),
        "workouts": data.get("workouts", []),
        "diet_plan": data.get("diet_plan", []),
        "water_intake": data.get("water_intake", 0),
        "sleep_schedule": data.get("sleep_schedule", {})
    }
    workout_logs.insert_one(log_entry)
    return jsonify({"success": True, "message": "Plan logged successfully"})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

# =============================================================
# Data Sync Endpoints (Local Storage Sync)
# =============================================================
@app.route('/api/sync-data', methods=['POST'])
def sync_data():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "User not logged in"}), 401
        
    if not is_mongodb_connected():
        return jsonify({"success": False, "message": "Database not connected."}), 503
        
    user_email = session.get('user_email')
    req_data = request.json or {}
    page_context = req_data.get('pageContext', 'user')
    payload = req_data.get('payload', {})
    
    # Restrict collections to safe alphanumeric boundaries
    import re
    safe_page_name = re.sub(r'[^a-zA-Z0-9]', '', page_context)
    if not safe_page_name:
        safe_page_name = "user"
        
    collection_name = f"{safe_page_name}_data"
    
    # Store dynamic schema
    update_doc = {
        "user_email": user_email,
        "last_synced": datetime.now(timezone.utc),
    }
    
    # We dynamically flat-update the 'data' subdocument
    set_ops = {"last_synced": update_doc["last_synced"]}
    for k, v in payload.items():
        set_ops[f"data.{k}"] = v
        
    # Upsert the user data specifically for this page module
    db[collection_name].update_one(
        {"user_email": user_email},
        {"$set": set_ops, "$setOnInsert": {"user_email": user_email}},
        upsert=True
    )
    
    return jsonify({"success": True, "message": "Data synchronized successfully"}), 200

@app.route('/api/get-data', methods=['GET'])
def get_data():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "User not logged in", "data": {}}), 401
        
    if not is_mongodb_connected():
        return jsonify({"success": False, "message": "Database not connected.", "data": {}}), 503
        
    user_email = session.get('user_email')
    
    merged_data = {}
    
    # Safe whitelist of pages we know. Adds a fallback generic 'user_data' check.
    page_prefixes = ['index', 'game', 'stat', 'goal', 'plan', 'sports', 'aura', 'leader', 'login', 'login1', 'ai', 'aicoach', 'aivoice', 'workout', 'user']
    
    for page in page_prefixes:
        c_name = f"{page}_data"
        if c_name in db.list_collection_names():
            doc = db[c_name].find_one({"user_email": user_email})
            if doc and "data" in doc:
                merged_data.update(doc["data"])
    
    return jsonify({"success": True, "data": merged_data}), 200


if __name__ == '__main__':
    # Only open browser if not in debug reloader
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Start browser opening in a separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=True)