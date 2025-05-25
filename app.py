import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_mail import Mail

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Define base model class
class Base(DeclarativeBase):
    pass

# Create app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "invoicemanagersecretkey")
app.config['WTF_CSRF_ENABLED'] = True
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Context processor
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///invoice_manager.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize extensions
db = SQLAlchemy(app, model_class=Base)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
mail = Mail(app)

# Initialize models
import models
models_dict = models.init_models(db)
User = models_dict['User']
Customer = models_dict['Customer']
Invoice = models_dict['Invoice']
InvoiceItem = models_dict['InvoiceItem']

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

# Import routes after models are initialized
import routes