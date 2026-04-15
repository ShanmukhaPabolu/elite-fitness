# C:\Users\rishi\Desktop\fitness\auth.py

from flask import Blueprint, request, jsonify, redirect, url_for, session
import requests
import os
from functools import wraps

auth_blueprint = Blueprint('auth', __name__)

# --- Configuration ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your_actual_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your_actual_client_secret")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/api/auth/google/callback")

FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "YOUR_FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "YOUR_FACEBOOK_APP_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI", "http://127.0.0.1:5000/api/auth/facebook/callback")

# --- Helper Functions ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return jsonify({"success": False, "message": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Google OAuth Routes ---
@auth_blueprint.route('/google')
def google_login():
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"scope=openid%20email%20profile&"
        f"response_type=code"
    )
    return redirect(auth_url)

@auth_blueprint.route('/google/callback')
def google_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"success": False, "message": "Failed to get Google authorization code."}), 400

    token_url = "https://accounts.google.com/o/oauth2/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        access_token = token_info.get("access_token")

        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_info_response = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'})
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        email = user_info.get('email')
        name = user_info.get('name', user_info.get('given_name', 'User'))
        
        try:
            from app import users_collection
            import datetime
            if users_collection is not None and email:
                existing_user = users_collection.find_one({"email": email})
                if not existing_user:
                    users_collection.insert_one({
                        "name": name,
                        "email": email,
                        "auth_provider": "google",
                        "created_at": datetime.datetime.now(datetime.timezone.utc)
                    })
        except ImportError:
            pass
            
        session['logged_in'] = True
        session['user_email'] = email
        session['user_name'] = name
        
        html_redirect = """
        <html><body><script>
        fetch('http://127.0.0.1:5000/api/get-data', {credentials: 'include'})
        .then(res => res.json())
        .then(syncData => {
            if(syncData.success && syncData.data) {
                for (let k in syncData.data) {
                    localStorage.setItem(k, syncData.data[k]);
                }
            }
            window.location.href = '/plan.html';
        }).catch(() => { window.location.href = '/plan.html'; });
        </script></body></html>
        """
        return html_redirect
    
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": f"Google auth error: {str(e)}"}), 500

# --- Facebook OAuth Routes ---
@auth_blueprint.route('/facebook')
def facebook_login():
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={FACEBOOK_APP_ID}&"
        f"redirect_uri={FACEBOOK_REDIRECT_URI}&"
        f"scope=email&"
        f"response_type=code"
    )
    return redirect(auth_url)

@auth_blueprint.route('/facebook/callback')
def facebook_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"success": False, "message": "Failed to get Facebook authorization code."}), 400
    
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    token_data = {
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": FACEBOOK_REDIRECT_URI,
        "client_secret": FACEBOOK_APP_SECRET,
        "code": code
    }

    try:
        response = requests.get(token_url, params=token_data)
        response.raise_for_status()
        token_info = response.json()
        access_token = token_info.get("access_token")

        user_info_url = f"https://graph.facebook.com/v19.0/me?fields=id,name,email&access_token={access_token}"
        user_info_response = requests.get(user_info_url)
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        email = user_info.get('email')
        name = user_info.get('name', 'User')
        
        try:
            from app import users_collection
            import datetime
            if users_collection is not None and email:
                existing_user = users_collection.find_one({"email": email})
                if not existing_user:
                    users_collection.insert_one({
                        "name": name,
                        "email": email,
                        "auth_provider": "facebook",
                        "created_at": datetime.datetime.now(datetime.timezone.utc)
                    })
        except ImportError:
            pass
            
        session['logged_in'] = True
        session['user_email'] = email
        session['user_name'] = name
        
        html_redirect = """
        <html><body><script>
        fetch('http://127.0.0.1:5000/api/get-data', {credentials: 'include'})
        .then(res => res.json())
        .then(syncData => {
            if(syncData.success && syncData.data) {
                for (let k in syncData.data) {
                    localStorage.setItem(k, syncData.data[k]);
                }
            }
            window.location.href = '/plan.html';
        }).catch(() => { window.location.href = '/plan.html'; });
        </script></body></html>
        """
        return html_redirect

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": f"Facebook auth error: {str(e)}"}), 500