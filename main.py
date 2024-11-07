from flask import Flask, request, jsonify, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, create_all, User
from utils import MailManager
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config['SECRET'] = os.getenv("SECRET")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

manager = MailManager()

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
    manager.build_email(user_id=new_user.id, user_mail=new_user.email, username=new_user.username, redirect_url=data['then'])
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
        pass
    elif manager.check_token(data['token']):
        user.confirmed = 1
    db.session.commit()
    return redirect(data['then'])


if __name__ == '__main__':
    app.run(debug=True)