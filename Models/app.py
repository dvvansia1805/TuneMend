from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Spotify Configuration
SPOTIFY_CLIENT_ID = '35f3a6c0414242fcae07c92b153b9853'
SPOTIFY_CLIENT_SECRET = 'b2469a8442a3498db01f57ba59cc9e87'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'

class MusicTherapyClassifier:
    def __init__(self):
        self.rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.playlist_mapping = {
            'Anxiety': '0eU3ubPAnqeSMi9K3YKVpC',
            'Depression': '6vEYfoIeIIzC87k94JDcYj',
            'OCD': '6CGI37QRfM5lsXjHs2cvv7',
            'Insomnia': '77Gf7zxkvSwKt53eLnXCLb'
        }

    def calculate_condition_scores(self, user_inputs):
        sleep_score = user_inputs['sleep_issues'] / 4
        mood_score = user_inputs['mood_changes'] / 3
        energy_score = (10 - user_inputs['energy_levels']) / 10
        concentration_score = user_inputs['concentration'] / 4
        intrusive_score = user_inputs['intrusive_thoughts'] / 4
        physical_score = user_inputs['physical_symptoms']
        social_score = user_inputs['social_engagement'] / 3
        
        scores = {
            'Anxiety': (intrusive_score * 0.3 +
                       physical_score * 0.2 +
                       social_score * 0.2 +
                       concentration_score * 0.15 +
                       sleep_score * 0.15),
            'Depression': (mood_score * 0.3 +
                          energy_score * 0.25 +
                          social_score * 0.2 +
                          sleep_score * 0.15 +
                          concentration_score * 0.1),
            'OCD': (intrusive_score * 0.4 +
                   concentration_score * 0.25 +
                   physical_score * 0.2 +
                   social_score * 0.15),
            'Insomnia': (sleep_score * 0.4 +
                        energy_score * 0.25 +
                        concentration_score * 0.2 +
                        physical_score * 0.15)
        }
        
        return scores

    def predict_condition(self, user_inputs):
        scores = self.calculate_condition_scores(user_inputs)
        predicted_condition = max(scores.items(), key=lambda x: x[1])[0]
        severity_score = (sum(scores.values()) / len(scores)) * 10
        recommendations = self.get_genre_recommendations(predicted_condition, severity_score)
        
        playlist_url = self.get_spotify_playlist(predicted_condition)
        
        return {
            'predicted_condition': predicted_condition,
            'severity_score': round(severity_score, 2),
            'condition_scores': {k: round(v * 10, 2) for k, v in scores.items()},
            'recommended_genres': recommendations,
            'playlist_url': playlist_url
        }

    def get_genre_recommendations(self, condition, severity):
        genre_mapping = {
            'Anxiety': ['Classical', 'Lofi', 'Jazz', 'Folk'],
            'Depression': ['Pop', 'Rock', 'Hip hop', 'R&B'],
            'OCD': ['Classical', 'Jazz', 'Video game music', 'Lofi'],
            'Insomnia': ['Classical', 'Lofi', 'Jazz', 'Folk']
        }
        
        return genre_mapping.get(condition, ['Classical', 'Jazz', 'Lofi'])

    def get_spotify_playlist(self, condition):
        playlist_id = self.playlist_mapping.get(condition)
        if not playlist_id:
            return None
        return f"https://open.spotify.com/embed/playlist/{playlist_id}"

@app.route('/')
def index1():
    return render_template('index1.html')

@app.route('/index2')
def index2():
    return render_template('index2.html')

@app.route('/index3')
def index3():
    return render_template('index3.html')

@app.route('/index4', methods=['GET', 'POST'])
def index4():
    if request.method == 'POST':
        user_inputs = {
            'sleep_issues': int(request.form['sleep_issues']),
            'mood_changes': int(request.form['mood_changes']),
            'energy_levels': int(request.form['energy_levels']),
            'concentration': int(request.form['concentration']),
            'intrusive_thoughts': int(request.form['intrusive_thoughts']),
            'physical_symptoms': int(request.form['physical_symptoms']),
            'social_engagement': int(request.form['social_engagement']),
        }
        classifier = MusicTherapyClassifier()
        result = classifier.predict_condition(user_inputs)
        return render_template("result.html", result=result)
    return render_template('index4.html')

@app.route('/get-started')
def get_started():
    return redirect(url_for('index2'))

@app.route('/submit', methods=['POST'])
def submit():
    return redirect(url_for('index4'))

@app.route('/login')
def login():
    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
        f"&scope=playlist-read-private"
    )
    return redirect(auth_url)

@app.route('/callback')
def spotify_callback():
    code = request.args.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    response = requests.post(
        token_url,
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SPOTIFY_REDIRECT_URI,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET
        }
    )
    token_data = response.json()
    session['access_token'] = token_data['access_token']
    return redirect(url_for('index2'))

if __name__ == "__main__":
    app.run(debug=True)