from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Global database reference
db = None

# Model placeholder classes for type hints
class User(UserMixin):
    id = None
    username = None
    email = None
    password_hash = None
    
    def set_password(self, password):
        pass
        
    def check_password(self, password):
        return False

class Customer:
    id = None
    name = None
    email = None
    address = None
    phone = None
    user_id = None
    created_at = None

class Invoice:
    id = None
    invoice_number = None
    date_issued = None
    date_due = None
    status = None
    notes = None
    tax_rate = None
    subtotal = None
    tax_amount = None
    total = None
    user_id = None
    customer_id = None
    created_at = None
    updated_at = None

class InvoiceItem:
    id = None
    description = None
    quantity = None
    unit_price = None
    amount = None
    invoice_id = None
    created_at = None

def init_models(database):
    global db
    db = database
    
    # Define real model classes with database connection
    class RealUser(UserMixin, db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(64), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(256), nullable=False)
        business_name = db.Column(db.String(120))
        business_address = db.Column(db.String(256))
        business_phone = db.Column(db.String(20))
        business_logo_url = db.Column(db.String(256))
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Relationships
        invoices = db.relationship('RealInvoice', backref='user', lazy=True, cascade="all, delete-orphan")
        
        def set_password(self, password):
            self.password_hash = generate_password_hash(password)
            
        def check_password(self, password):
            return check_password_hash(self.password_hash, password)
    
    class RealCustomer(db.Model):
        __tablename__ = 'customers'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(120), nullable=False)
        email = db.Column(db.String(120))
        address = db.Column(db.String(256))
        phone = db.Column(db.String(20))
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Relationships
        invoices = db.relationship('RealInvoice', backref='customer', lazy=True)
    
    class RealInvoice(db.Model):
        __tablename__ = 'invoices'
        id = db.Column(db.Integer, primary_key=True)
        invoice_number = db.Column(db.String(20), nullable=False)
        date_issued = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
        date_due = db.Column(db.Date, nullable=False)
        status = db.Column(db.String(20), default='Unpaid')  # Paid, Unpaid, Overdue, Cancelled
        notes = db.Column(db.Text)
        tax_rate = db.Column(db.Float, default=0.0)
        subtotal = db.Column(db.Float, default=0.0)
        tax_amount = db.Column(db.Float, default=0.0)
        total = db.Column(db.Float, default=0.0)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # Relationships
        items = db.relationship('RealInvoiceItem', backref='invoice', lazy=True, cascade="all, delete-orphan")
    
    class RealInvoiceItem(db.Model):
        __tablename__ = 'invoice_items'
        id = db.Column(db.Integer, primary_key=True)
        description = db.Column(db.String(256), nullable=False)
        quantity = db.Column(db.Float, nullable=False, default=1.0)
        unit_price = db.Column(db.Float, nullable=False, default=0.0)
        amount = db.Column(db.Float, nullable=False, default=0.0)
        invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Update global references
    global User, Customer, Invoice, InvoiceItem
    User = RealUser
    Customer = RealCustomer
    Invoice = RealInvoice
    InvoiceItem = RealInvoiceItem
    
    # Return model dictionary
    return {
        'User': RealUser,
        'Customer': RealCustomer,
        'Invoice': RealInvoice,
        'InvoiceItem': RealInvoiceItem
    }