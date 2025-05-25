from flask import render_template, url_for, flash, redirect, request, jsonify, send_file
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash
from app import app, db, mail
from app import User, Customer, Invoice, InvoiceItem
from forms import RegistrationForm, LoginForm, CustomerForm, InvoiceForm, ProfileForm
from datetime import datetime, timedelta
import io
import json
from flask_mail import Message
from utils import generate_pdf

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            business_name=form.business_name.data,
            business_address=form.business_address.data,
            business_phone=form.business_phone.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

# routes.py dosyasının geri kalanını mevcut kodunuzdan kopyalayın, sadece import kısmını değiştirin
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent invoices (last 10)
    recent_invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).limit(10).all()
    
    # Get statistics
    total_invoices = Invoice.query.filter_by(user_id=current_user.id).count()
    paid_invoices = Invoice.query.filter_by(user_id=current_user.id, status='Paid').count()
    unpaid_invoices = Invoice.query.filter_by(user_id=current_user.id, status='Unpaid').count()
    overdue_invoices = Invoice.query.filter_by(user_id=current_user.id, status='Overdue').count()
    
    # Calculate total revenue (sum of paid invoices)
    revenue = 0
    paid_invoice_list = Invoice.query.filter_by(user_id=current_user.id, status='Paid').all()
    for invoice in paid_invoice_list:
        revenue += invoice.total
    
    # Get customer count
    customer_count = Customer.query.filter_by(user_id=current_user.id).count()
    
    return render_template(
        'dashboard.html', 
        title='Dashboard',
        recent_invoices=recent_invoices,
        total_invoices=total_invoices,
        paid_invoices=paid_invoices,
        unpaid_invoices=unpaid_invoices,
        overdue_invoices=overdue_invoices,
        revenue=revenue,
        customer_count=customer_count
    )

@app.route('/invoices')
@login_required
def invoices():
    status_filter = request.args.get('status', '')
    
    if status_filter and status_filter != 'All':
        invoices = Invoice.query.filter_by(user_id=current_user.id, status=status_filter).order_by(Invoice.created_at.desc()).all()
    else:
        invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).all()
    
    return render_template('dashboard.html', 
                          title='Invoices', 
                          invoices=invoices, 
                          active_tab='invoices',
                          status_filter=status_filter)

@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    form = CustomerForm()
    
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            email=form.email.data,
            address=form.address.data,
            phone=form.phone.data,
            user_id=current_user.id
        )
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    
    customers_list = Customer.query.filter_by(user_id=current_user.id).order_by(Customer.name).all()
    
    return render_template('dashboard.html', 
                          title='Customers', 
                          customers=customers_list, 
                          form=form,
                          active_tab='customers')

@app.route('/customer/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Make sure the customer belongs to the current user
    if customer.user_id != current_user.id:
        flash('You do not have permission to edit this customer.', 'danger')
        return redirect(url_for('customers'))
    
    form = CustomerForm()
    
    if form.validate_on_submit():
        customer.name = form.name.data
        customer.email = form.email.data
        customer.address = form.address.data
        customer.phone = form.phone.data
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers'))
    
    # Pre-fill form with customer data
    if request.method == 'GET':
        form.name.data = customer.name
        form.email.data = customer.email
        form.address.data = customer.address
        form.phone.data = customer.phone
    
    return render_template('dashboard.html', 
                          title='Edit Customer', 
                          form=form, 
                          customer=customer,
                          active_tab='customers',
                          editing=True)

@app.route('/customer/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Make sure the customer belongs to the current user
    if customer.user_id != current_user.id:
        flash('You do not have permission to delete this customer.', 'danger')
        return redirect(url_for('customers'))
    
    # Check if the customer has invoices
    if customer.invoices:
        flash('Cannot delete customer with associated invoices.', 'danger')
        return redirect(url_for('customers'))
    
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/create_invoice', methods=['GET', 'POST'])
@login_required
def create_invoice():
    form = InvoiceForm()
    
    # Get customer list for dropdown
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    form.customer_id.choices = [(c.id, c.name) for c in customers]
    
    # Generate next invoice number
    last_invoice = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.id.desc()).first()
    next_invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-001"
    if last_invoice:
        # Extract the sequence number and increment
        parts = last_invoice.invoice_number.split('-')
        if len(parts) == 3 and parts[0] == 'INV' and parts[1] == datetime.now().strftime('%Y%m'):
            next_seq = int(parts[2]) + 1
            next_invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{next_seq:03d}"
    
    if request.method == 'POST':
        try:
            # Extract form data manually
            invoice_number = request.form.get('invoice_number')
            date_issued_str = request.form.get('date_issued')
            date_due_str = request.form.get('date_due')
            customer_id_str = request.form.get('customer_id')
            tax_rate_str = request.form.get('tax_rate', '0')
            notes = request.form.get('notes', '')
            status = request.form.get('status', 'Unpaid')
            subtotal_str = request.form.get('subtotal', '0')
            tax_amount_str = request.form.get('tax_amount', '0')
            total_str = request.form.get('total', '0')
            
            # Convert to proper types with validation
            if not date_issued_str:
                raise ValueError("Fatura tarihi gereklidir")
            date_issued = datetime.strptime(date_issued_str, '%Y-%m-%d').date()
            
            if not date_due_str:
                raise ValueError("Son ödeme tarihi gereklidir")
            date_due = datetime.strptime(date_due_str, '%Y-%m-%d').date()
            
            if not customer_id_str:
                raise ValueError("Müşteri seçilmelidir")
            customer_id = int(customer_id_str)
            
            tax_rate = float(tax_rate_str)
            subtotal = float(subtotal_str)
            tax_amount = float(tax_amount_str)
            total = float(total_str)
            
            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                date_issued=date_issued,
                date_due=date_due,
                customer_id=customer_id,
                tax_rate=tax_rate,
                notes=notes,
                status=status,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total=total,
                user_id=current_user.id
            )
            db.session.add(invoice)
            db.session.flush()  # Get the invoice ID
            
            # Get all form keys to find item fields
            keys = list(request.form.keys())
            item_indices = set()
            
            # Extract item indices from form keys
            for key in keys:
                if key.startswith('items-') and '-description' in key:
                    # Format: items-{index}-description
                    parts = key.split('-')
                    if len(parts) == 3:
                        item_indices.add(parts[1])
            
            # Add invoice items
            for idx in item_indices:
                desc_key = f'items-{idx}-description'
                qty_key = f'items-{idx}-quantity'
                price_key = f'items-{idx}-unit_price'
                amount_key = f'items-{idx}-amount'
                
                description = request.form.get(desc_key, '')
                quantity_str = request.form.get(qty_key, '0')
                unit_price_str = request.form.get(price_key, '0')
                amount_str = request.form.get(amount_key, '0')
                
                # Skip empty rows
                if not description.strip():
                    continue
                    
                quantity = float(quantity_str)
                unit_price = float(unit_price_str)
                amount = float(amount_str)
                
                item = InvoiceItem(
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount,
                    invoice_id=invoice.id
                )
                db.session.add(item)
            
            db.session.commit()
            flash('Fatura başarıyla oluşturuldu!', 'success')
            return redirect(url_for('view_invoice', invoice_id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Fatura oluşturulurken bir hata oluştu: {str(e)}', 'danger')
            print(f"Error creating invoice: {str(e)}")
    
    # Pre-fill form data
    if request.method == 'GET':
        form.invoice_number.data = next_invoice_number
        form.date_issued.data = datetime.now().date()
        form.date_due.data = (datetime.now() + timedelta(days=30)).date()
    
    return render_template('create_invoice.html', title='Create Invoice', form=form)

@app.route('/invoice/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Make sure the invoice belongs to the current user
    if invoice.user_id != current_user.id:
        flash('You do not have permission to view this invoice.', 'danger')
        return redirect(url_for('invoices'))
    
    return render_template('view_invoice.html', title='View Invoice', invoice=invoice)

@app.route('/invoice/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Make sure the invoice belongs to the current user
    if invoice.user_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoices'))
    
    form = InvoiceForm()
    
    # Get customer list for dropdown
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    form.customer_id.choices = [(c.id, c.name) for c in customers]
    
    if request.method == 'POST':
        try:
            # Extract form data manually
            invoice_number = request.form.get('invoice_number')
            date_issued_str = request.form.get('date_issued')
            date_due_str = request.form.get('date_due')
            customer_id_str = request.form.get('customer_id')
            tax_rate_str = request.form.get('tax_rate', '0')
            notes = request.form.get('notes', '')
            status = request.form.get('status', 'Unpaid')
            subtotal_str = request.form.get('subtotal', '0')
            tax_amount_str = request.form.get('tax_amount', '0')
            total_str = request.form.get('total', '0')
            
            # Convert to proper types with validation
            if not date_issued_str:
                raise ValueError("Issue date is required")
            date_issued = datetime.strptime(date_issued_str, '%Y-%m-%d').date()
            
            if not date_due_str:
                raise ValueError("Due date is required")
            date_due = datetime.strptime(date_due_str, '%Y-%m-%d').date()
            
            if not customer_id_str:
                raise ValueError("Customer must be selected")
            customer_id = int(customer_id_str)
            
            tax_rate = float(tax_rate_str)
            subtotal = float(subtotal_str)
            tax_amount = float(tax_amount_str)
            total = float(total_str)
            
            # Update invoice
            invoice.invoice_number = invoice_number
            invoice.date_issued = date_issued
            invoice.date_due = date_due
            invoice.customer_id = customer_id
            invoice.tax_rate = tax_rate
            invoice.notes = notes
            invoice.status = status
            invoice.subtotal = subtotal
            invoice.tax_amount = tax_amount
            invoice.total = total
            
            # Delete existing items
            for item in invoice.items:
                db.session.delete(item)
            
            # Get all form keys to find item fields
            keys = list(request.form.keys())
            item_indices = set()
            
            # Extract item indices from form keys
            for key in keys:
                if key.startswith('items-') and '-description' in key:
                    # Format: items-{index}-description
                    parts = key.split('-')
                    if len(parts) == 3:
                        item_indices.add(parts[1])
            
            # Add invoice items
            for idx in item_indices:
                desc_key = f'items-{idx}-description'
                qty_key = f'items-{idx}-quantity'
                price_key = f'items-{idx}-unit_price'
                amount_key = f'items-{idx}-amount'
                
                description = request.form.get(desc_key, '')
                quantity_str = request.form.get(qty_key, '0')
                unit_price_str = request.form.get(price_key, '0')
                amount_str = request.form.get(amount_key, '0')
                
                # Skip empty rows
                if not description.strip():
                    continue
                    
                quantity = float(quantity_str)
                unit_price = float(unit_price_str)
                amount = float(amount_str)
                
                item = InvoiceItem(
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount,
                    invoice_id=invoice.id
                )
                db.session.add(item)
            
            db.session.commit()
            flash('Invoice updated successfully!', 'success')
            return redirect(url_for('view_invoice', invoice_id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating invoice: {str(e)}', 'danger')
            print(f"Error updating invoice: {str(e)}")
    
    # Pre-fill form with invoice data (for the form itself)
    if request.method == 'GET':
        form.invoice_number.data = invoice.invoice_number
        form.date_issued.data = invoice.date_issued
        form.date_due.data = invoice.date_due
        form.customer_id.data = invoice.customer_id
        form.tax_rate.data = invoice.tax_rate
        form.notes.data = invoice.notes
        form.status.data = invoice.status
        form.subtotal.data = invoice.subtotal
        form.tax_amount.data = invoice.tax_amount
        form.total.data = invoice.total
    
    # Use our fixed template instead
    return render_template('edit_invoice_fix.html', title='Edit Invoice', form=form, invoice=invoice)

@app.route('/invoice/<int:invoice_id>/delete', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Make sure the invoice belongs to the current user
    if invoice.user_id != current_user.id:
        flash('You do not have permission to delete this invoice.', 'danger')
        return redirect(url_for('invoices'))
    
    db.session.delete(invoice)
    db.session.commit()
    flash('Invoice deleted successfully!', 'success')
    return redirect(url_for('invoices'))

@app.route('/invoice/<int:invoice_id>/pdf')
@login_required
def download_invoice_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Make sure the invoice belongs to the current user
    if invoice.user_id != current_user.id:
        flash('You do not have permission to download this invoice.', 'danger')
        return redirect(url_for('invoices'))
    
    # Generate PDF
    pdf_file = generate_pdf(invoice)
    
    # Return PDF as a downloadable file
    return send_file(
        io.BytesIO(pdf_file),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Invoice-{invoice.invoice_number}.pdf"
    )

@app.route('/invoice/<int:invoice_id>/send', methods=['POST'])
@login_required
def send_invoice_email(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Make sure the invoice belongs to the current user
    if invoice.user_id != current_user.id:
        flash('You do not have permission to send this invoice.', 'danger')
        return redirect(url_for('invoices'))
    
    # Check if customer has email
    if not invoice.customer.email:
        flash('Customer does not have an email address.', 'danger')
        return redirect(url_for('view_invoice', invoice_id=invoice.id))
    
    # Generate PDF
    pdf_file = generate_pdf(invoice)
    
    # Create email
    msg = Message(
        subject=f"Invoice {invoice.invoice_number} from {current_user.business_name or current_user.username}",
        recipients=[invoice.customer.email]
    )
    
    msg.body = f"""
Dear {invoice.customer.name},

Please find attached your invoice {invoice.invoice_number} for the amount of ${invoice.total:.2f}.

Due date: {invoice.date_due.strftime('%B %d, %Y')}

Thank you for your business.

Best regards,
{current_user.business_name or current_user.username}
"""
    
    # Attach PDF
    msg.attach(
        f"Invoice-{invoice.invoice_number}.pdf",
        "application/pdf",
        pdf_file
    )
    
    # Send email
    try:
        mail.send(msg)
        flash('Invoice sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'danger')
    
    return redirect(url_for('view_invoice', invoice_id=invoice.id))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if form.validate_on_submit():
        # Check if username is being changed and is already taken
        if form.username.data != current_user.username and User.query.filter_by(username=form.username.data).first():
            flash('Username already taken!', 'danger')
            return redirect(url_for('profile'))
        
        # Check if email is being changed and is already taken
        if form.email.data != current_user.email and User.query.filter_by(email=form.email.data).first():
            flash('Email already taken!', 'danger')
            return redirect(url_for('profile'))
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.business_name = form.business_name.data
        current_user.business_address = form.business_address.data
        current_user.business_phone = form.business_phone.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    
    # Pre-fill form with user data
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.business_name.data = current_user.business_name
        form.business_address.data = current_user.business_address
        form.business_phone.data = current_user.business_phone
    
    return render_template('dashboard.html', 
                          title='Profile', 
                          form=form,
                          active_tab='profile')
