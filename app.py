import os
import logging
from functools import wraps

from flask import Flask, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__, static_folder="templates/static", static_url_path="/static")
app.secret_key = os.environ.get("SESSION_SECRET") or os.urandom(32).hex()
app.config["LOGIN_PASSWORD"] = os.environ.get("LOGIN_PASSWORD", "MK-KING")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "0") == "1"

@app.before_request
def require_login():
    # Allow the login page and static assets; protect the dashboard and every API.
    if request.endpoint in {"login", "static"} or request.path.startswith("/static/"):
        return None
    if not session.get("authenticated"):
        if request.path.startswith("/api/"):
            return {"success": False, "error": "Authentication required"}, 401
        return redirect(url_for("login"))
    return None
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS for API endpoints
CORS(app)

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///quotex_signals.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models and routes
    import models
    import routes
    
    # Create all tables
    db.create_all()
