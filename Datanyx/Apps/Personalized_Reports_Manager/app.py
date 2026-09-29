"""Personalized Reports Manager - Flask Application Entry Point.

This file creates the Flask app, registers the API blueprint from routes.py,
and serves the React frontend. All route logic is in routes.py; all DB
utilities are in db.py; all config/constants are in config.py; and all
report generation logic is in generators.py.
"""
from flask import Flask, render_template
from routes import bp


app = Flask(__name__)
app.register_blueprint(bp)


@app.route('/')
def home():
    """Serve the React frontend."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
