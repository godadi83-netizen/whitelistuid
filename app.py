from flask import Flask, redirect, url_for, session, request, render_template_string
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "TITAN_SECURE_RANDOM_KEY_999"

# ⚠️ आपकी Discord डेवलपर और वेबहुक डिटेल्स (बिलकुल सही फॉर्मेट में)
CLIENT_ID = "1537547951076024440"
CLIENT_SECRET = "X40CFd5tfrmeAgHtTsei5BZJw4UjpUw0"
REDIRECT_URI = "https://titanexeuidbypss-1.onrender.com/callback"  # Render का लाइव लिंक
DISCORD_API_ENDPOINT = "https://discord.com/api/v10"
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1537548668612116510/8xjXIW0jDwFaU9XD0bsaa0wqPCfX6F65X8X3lPn-0SJ8LbiAeOe4lEdZvLvL3Yc9rYVI"

# 24 घंटे का कूलडाउन ट्रैक करने के लिए डिक्शनरी
USER_COOLDOWNS = {}

@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(LOGIN_HTML)
    
    user_id = session['user']['id']
    
    # कूलडाउन चेक
    if user_id in USER_COOLDOWNS:
        last_time = USER_COOLDOWNS[user_id]
        time_diff = datetime.now() - last_time
        if time_diff < timedelta(hours=24):
            remaining_hours = 24 - int(time_diff.total_seconds() / 3600)
            return render_template_string(COOLDOWN_HTML, hours=remaining_hours, user=session['user'])
            
    return render_template_string(PANEL_HTML, user=session['user'])

@app.route('/login')
def login():
    discord_login_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Authorization failed!", 400
        
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(f"{DISCORD_API_ENDPOINT}/oauth2/token", data=data, headers=headers)
    credentials = response.json()
    access_token = credentials.get('access_token')
    
    if not access_token:
        return "Failed to get access token from Discord.", 400
        
    user_response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me", headers={'Authorization': f'Bearer {access_token}'})
    user_data = user_response.json()
    
    session['user'] = {
        'username': user_data.get('username'),
        'id': user_data.get('id')
    }
    
    return redirect(url_for('home'))

@app.route('/submit', methods=['POST'])
def submit():
    if 'user' not in session:
        return redirect(url_for('home'))
        
    user = session['user']
    user_id = user['id']
    
    if user_id in USER_COOLDOWNS:
        if datetime.now() - USER_COOLDOWNS[user_id] < timedelta(hours=24):
            return redirect(url_for('home'))
            
    uid = request.form.get('uid')
    player_name = request.form.get('player_name')
    region = request.form.get('region')
    
    # कूलडाउन सेट करना
    USER_COOLDOWNS[user_id] = datetime.now()
    
    # Discord Webhook पेलोड
    discord_payload = {
        "content": f"🔔 Whitelist claimed by verified user: <@{user_id}>",
        "embeds": [{
            "title": "⚡ UID WHITELIST ADDED (VERIFIED)",
            "color": 5793266,
            "fields": [
                {"name": "🎯 Target UID", "value": f"`{uid}`", "inline": True},
                {"name": "👤 Real Player Name", "value": f"`{player_name}`", "inline": True},
                {"name": "🌍 Region", "value": f"`{region}`", "inline": True},
                {"name": "⏳ Validity", "value": "`2 Days Free`", "inline": True},
                {"name": "💬 Verified Discord", "value": f"@{user['username']} (ID: {user_id})", "inline": False}
            ],
            "footer": {"text": "TITAN EXE SECURE GATEWAY • PREMIUM"}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)
    
    return render_template_string(SUCCESS_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- PREMIUM HTML TEMPLATES ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Titan Security - Discord Login</title>
    <style>
        body { background: #07090e; color: #fff; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #111622; border: 1px solid #1f293d; padding: 40px; border-radius: 16px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.5); width: 380px; }
        h1 { font-size: 22px; margin-bottom: 10px; color: #5865F2; }
        p { color: #8b949e; font-size: 14px; margin-bottom: 30px; }
        .btn { background: #5865F2; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block; transition: 0.3s; width: 100%; box-sizing: border-box; }
        .btn:hover { background: #4752C4; box-shadow: 0 0 15px rgba(88,101,242,0.4); }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>🛡️ TITAN EXE GATEWAY</h1>
        <p>Authenticate with your verified Discord account to access the whitelist management system.</p>
        <a href="/login" class="btn">🎮 Login with Discord</a>
    </div>
</body>
</html>
"""

PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Whitelist Management Panel</title>
    <style>
        body { background: #07090e; color: #fff; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .panel-card { background: #111622; border: 1px solid #1f293d; padding: 35px; border-radius: 16px; width: 420px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #1f293d; padding-bottom: 15px; }
        h2 { font-size: 18px; margin: 0; color: #fff; }
        .user-tag { color: #3fb950; font-size: 13px; font-weight: 600; }
        .logout { color: #f85149; font-size: 13px; text-decoration: none; }
        label { font-size: 13px; font-weight: 600; color: #8b949e; display: block; margin-bottom: 6px; }
        input, select { width: 100%; padding: 10px 14px; background: #07090e; border: 1px solid #1f293d; border-radius: 8px; color: #fff; margin-bottom: 16px; box-sizing: border-box; font-size: 14px; }
        input:focus, select:focus { border-color: #3fb950; outline: none; }
        .btn-submit { background: #238636; color: white; border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: 600; font-size: 15px; cursor: pointer; transition: 0.3s; }
        .btn-submit:hover { background: #2ea043; box-shadow: 0 0 15px rgba(35,134,54,0.4); }
    </style>
</head>
<body>
    <div class="panel-card">
        <div class="header">
            <h2>🛡️ TITAN WL PANEL</h2>
            <div>
                <span class="user-tag">@{{ user.username }}</span> | 
                <a href="/logout" class="logout">Logout</a>
            </div>
        </div>
        
        <form action="/submit" method="POST">
            <label>UID *</label>
            <input type="text" name="uid" required placeholder="Enter Game UID">
            
            <label>Real Player Name *</label>
            <input type="text" name="player_name" required placeholder="Enter Verified Name">
            
            <label>Region *</label>
            <select name="region">
                <option>ALL SERVER</option>
                <option>IND</option>
                <option>BR</option>
                <option>US</option>
                <option>SG</option>
            </select>
            
            <label>Validity (Days)</label>
            <input type="text" value="2 Days Free" disabled style="color: #6e7681; cursor: not-allowed;">
            
            <button type="submit" class="btn-submit">Add UID to Whitelist</button>
        </form>
    </div>
</body>
</html>
"""

COOLDOWN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cooldown Active</title>
    <style>
        body { background: #07090e; color: #fff; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1a0f12; border: 1px solid #da3633; padding: 40px; border-radius: 16px; text-align: center; width: 400px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
        h2 { color: #f85149; margin-top: 0; }
        p { color: #c9d1d9; font-size: 14px; line-height: 1.6; }
        .highlight { color: #f85149; font-weight: bold; }
        .btn-out { background: #da3633; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>⏳ COOLDOWN ACTIVE</h2>
        <p>Hey <b style="color:white;">@{{ user.username }}</b>, you have already whitelisted an UID recently!</p>
        <p class="highlight">Try after 24 hours.</p>
        <hr style="border-color: #da3633; opacity: 0.3; margin: 20px 0;">
        <p>🔥 <b>Want free credit right now?</b><br>Invite 2 members to our Discord server and send the screenshot (ss) to the admin!</p>
        <a href="/logout" class="btn-out">Logout</a>
    </div>
</body>
</html>
"""

SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Success</title>
    <style>
        body { background: #07090e; color: #fff; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #111622; border: 1px solid #238636; padding: 40px; border-radius: 16px; text-align: center; width: 380px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
        h2 { color: #3fb950; margin-top: 0; }
        p { color: #8b949e; font-size: 14px; margin-bottom: 25px; }
        .btn-back { background: #238636; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block; }
    </style>
</head>
<body>
    <div class="card">
        <h2>✅ SUCCESSFUL!</h2>
        <p>UID successfully whitelisted and securely transmitted to Discord.</p>
        <a href="/" class="btn-back">Back to Panel</a>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)