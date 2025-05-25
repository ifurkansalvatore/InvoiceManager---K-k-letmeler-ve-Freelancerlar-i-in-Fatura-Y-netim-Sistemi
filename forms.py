from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, DateField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    business_name = StringField('Business Name', validators=[Optional(), Length(max=120)])
    business_address = TextAreaField('Business Address', validators=[Optional(), Length(max=256)])
    business_phone = StringField('Business Phone', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=256)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Save Customer')

class InvoiceItemForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired(), Length(max=256)])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    unit_price = FloatField('Unit Price', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])

class InvoiceForm(FlaskForm):
    invoice_number = StringField('Invoice Number', validators=[DataRequired(), Length(max=20)])
    date_issued = DateField('Date Issued', validators=[DataRequired()], format='%Y-%m-%d')
    date_due = DateField('Date Due', validators=[DataRequired()], format='%Y-%m-%d')
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    tax_rate = FloatField('Tax Rate (%)', validators=[Optional()], default=0.0)
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)])
    status = SelectField('Status', choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Overdue', 'Overdue'), ('Cancelled', 'Cancelled')])
    items = FieldList(FormField(InvoiceItemForm), min_entries=1)
    subtotal = FloatField('Subtotal', validators=[DataRequired()], default=0.0)
    tax_amount = FloatField('Tax Amount', validators=[DataRequired()], default=0.0)
    total = FloatField('Total', validators=[DataRequired()], default=0.0)
    submit = SubmitField('Save Invoice')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    business_name = StringField('Business Name', validators=[Optional(), Length(max=120)])
    business_address = TextAreaField('Business Address', validators=[Optional(), Length(max=256)])
    business_phone = StringField('Business Phone', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Update Profile')
