from flask import Flask, flash, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from database import db, create_all, User
from utils import Manager
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

manager = Manager()

with app.app_context():
    create_all(app)


@app.route('/')
def home():
    return jsonify({'message': 'Operating...'}), 200


@app.route('/register', methods=['POST'])
def register():
    data = request.args.to_dict()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.confirmed == 1:  # user exists and confirmed
        return jsonify({'message': 'Already registered!'}), 400
    hashed_password = generate_password_hash(data['password'], "pbkdf2:sha256", 8)
    if not user:  # new user
        new_user = User(
            email=data['email'],
            password=hashed_password,
            username=data['username'],
            token=manager.generate_token(expire=manager.valid_hours*3600)
        )
        db.session.add(new_user)
    else:  # user exists but not confirmed
        user.password = hashed_password
        user.username = data['username']
        user.token = manager.generate_token(expire=manager.valid_hours*3600)
        new_user = user
    db.session.commit()
    mail = manager.create_mail(user_mail=new_user.email, user_id=new_user.id, redirect_url=data['then'], task='confirm', username=new_user.username)
    mail.build_email()
    mail.send_email()
    return jsonify({'message': f'Registration successful! Please confirm your account by clicking the link in the email we sent to {new_user.email}.'}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.args.to_dict()
    user = User.query.filter_by(email=data['email']).first()
    if not user.confirmed:
        return jsonify({'message': 'Please confirm your email address first.'}), 401
    if user and check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login successful!'}), 200
    return jsonify({'message': 'Invalid credentials!'}), 401


@app.route('/confirm', methods=['GET'])
def confirm():
    data = request.args.to_dict()
    user = User.query.get(data['id'])
    if user and user.confirmed == 1:
        return jsonify({'message': 'Already confirmed!'}), 400
    if not user or not manager.check_token(data['token']):
        flash("Invalid confirmation link! You need to register again.")
        return render_template('redirect.html', redirect_url=data['then'])
    user.confirmed = 1
    db.session.commit()
    flash("Account confirmation successful!")
    return render_template('redirect.html', redirect_url=data['then'])


@app.route('/reset', methods=['POST'])
def reset_request():
    data = request.args.to_dict()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        user.token = manager.generate_token(expire=manager.valid_hours*3600)
        db.session.commit()
        mail = manager.create_mail(user_mail=user.email, user_id=user.id, redirect_url=data['then'], task='reset', username=user.username)
        mail.build_email()
        mail.send_email()
        return jsonify({'message': f'Password reset email sent to {user.email}.'}), 200
    return jsonify({'message': 'Invalid email address!'}), 400


@app.route('/reset', methods=['GET'])
def reset_open():
    data = request.args.to_dict()
    user = User.query.get(data['id'])
    if not user or not manager.check_token(data['token']):
        flash("Invalid reset link! Please request a new one.")
        return render_template('redirect.html', redirect_url=data['then'])
    
    return render_template('reset.html', id=user.id, then=data['then'], token=data['token'])


@app.route('/password/reset', methods=['POST'])
def reset_submit():
    user = User.query.get(int(request.form.get('id')))
    if not user or not manager.check_token(request.form.get('token')):
        flash("Invalid reset link! Please request a new one.")
        return render_template('redirect.html', redirect_url=request.form.get('then'))
    user.password = generate_password_hash(request.form.get('password'), "pbkdf2:sha256", 8)
    manager.delete_token(request.form.get('token'))
    user.token = manager.generate_token(expire=manager.valid_hours*3600)
    db.session.commit()
    flash("Password reset successful!")
    return render_template('redirect.html', redirect_url=request.form.get('then'))


if __name__ == '__main__':
    app.run(debug=False)