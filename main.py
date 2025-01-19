import io
import json
from pathlib import Path
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    jsonify,
    send_file,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import *
from database import User as UserModel
from utils import Manager
from dotenv import load_dotenv
import os
from flask_rebar import Rebar
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = "You need to login first!"
login_manager.login_view = "/app/login"
login_manager.login_message_category = "danger"


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class User(UserMixin, UserModel):
    pass


manager = Manager()

rebar = Rebar()

api_registry = rebar.create_handler_registry(prefix="/api/")
app_registry = rebar.create_handler_registry(prefix="/app/")


with app.app_context():
    create_all(app)


@app.route("/")
def health():
    return jsonify({"message": "Operating..."}), 200


# API ENDPOINTS
@api_registry.handles("/register", method="POST")
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    valid_email, msg = manager.validate_email(data["email"], check_deliverability=True)
    if not valid_email:
        return jsonify({"message": f"{msg}"}), 400

    user = User.query.filter_by(email=valid_email).first()
    if user and user.confirmed == 1:
        return jsonify({"message": "Already registered!"}), 400

    hashed_password = generate_password_hash(data["password"], "pbkdf2:sha256", 8)
    if not user:
        new_user = User(
            email=valid_email,
            password=hashed_password,
            username=data["username"],
            token=manager.generate_token(expire=manager.valid_hours * 3600),
        )
        db.session.add(new_user)
    else:
        user.password = hashed_password
        user.username = data["username"]
        user.token = manager.generate_token(expire=manager.valid_hours * 3600)
        new_user = user

    db.session.commit()

    mail = manager.create_mail(
        user_mail=new_user.email,
        user_id=new_user.id,
        redirect_url=data["then"],
        task="api/account/confirm",
        username=new_user.username,
        token=new_user.token,
    )
    mail.build_email()
    mail.send_email()

    return (
        jsonify(
            {
                "message": f"Registration successful, {new_user.username}! Please verify your account by clicking the confirmation link in the email we have sent to {new_user.email}."
            }
        ),
        200,
    )


@api_registry.handles("/login", method="POST")
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    valid_email, msg = manager.validate_email(data["email"])
    if not valid_email:
        return jsonify({"message": f"{msg}"}), 400

    user = User.query.filter_by(email=valid_email).first()
    if not user:
        return jsonify({"message": "No account found!"}), 401
    if not user.confirmed:
        return jsonify({"message": "Please confirm your email address first."}), 401

    if check_password_hash(user.password, data["password"]):
        return jsonify({"message": f"Login successful, {user.username}!"}), 200

    return jsonify({"message": "Invalid credentials!"}), 401


@api_registry.handles("/apikey/verify", method="GET")
def verify_apikey():
    token = request.headers.get("Authorization")
    if token is None:
        return {"error": "No authorization header provided."}
    try:
        user_id, _ = token.split(".")
    except Exception:
        return {"error": "Invalid authorization header."}

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"message": "No user found!"}), 400
    if not user.confirmed:
        return jsonify({"message": "Please confirm your email address first."}), 401

    if check_password_hash(user.apikey, token):
        return jsonify({"message": "Verification successful!", "user_id": user_id}), 200

    return jsonify({"message": "Invalid credentials!"}), 401


@api_registry.handles("/apikey/create", method="POST")
def create_apikey():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    user = User.query.filter_by(id=data["id"]).first()

    if not user:
        return jsonify({"message": "No user found!"}), 400
    plain_key = f"{user.id}.{manager.generate_token()}"
    hashed_key = generate_password_hash(plain_key, "pbkdf2:sha256", 8)
    user.apikey = hashed_key

    db.session.commit()
    return (
        jsonify(
            {
                "message": f"API Key created successful! Use it in the API request Authorization header.",
                "data": plain_key,
            }
        ),
        200,
    )


@api_registry.handles("/account/confirm", method="GET")
def confirm():
    data = request.args.to_dict()
    user = User.query.get(data["id"])
    if user and user.confirmed == 1:
        return jsonify({"message": "Already confirmed!"}), 400
    if not user or not manager.check_token(data["token"]):
        flash("Invalid confirmation link! You need to register again.")
        return render_template("redirect.html", redirect_url=data["then"])

    user.confirmed = 1
    db.session.commit()
    flash("Account confirmation successful!")
    return render_template("redirect.html", redirect_url=data["then"])


@api_registry.handles("/email/confirm", method="GET")
@login_required
def confirm_email_change():
    data = request.args.to_dict()
    if not manager.check_token(data["token"]):
        flash("Invalid confirmation link!", "danger")
        return redirect(f"{request.url_root}/{app_registry.prefix}")

    current_user.email = session["pending_email"]
    session.pop("pending_email", None)
    db.session.commit()
    flash("Your email address has been updated successfully!", "success")

    return redirect(f"{request.url_root}/{app_registry.prefix}")


# APP ENDPOINTS
@app_registry.handles("/", method="GET")
def dashboard():
    return render_template("index.html")


@app_registry.handles("/login", method="GET")
def get_login():
    if current_user.is_authenticated:
        flash("Already logged in!", "danger")
        return redirect(f"{request.url_root}/{app_registry.prefix}")

    return render_template("login.html")


@app_registry.handles("/login", method="POST")
def post_login():
    data = request.form

    valid_email, msg = manager.validate_email(data["email"])
    if not valid_email:
        flash(f"{msg}", "danger")
        return redirect(request.url)

    user = User.query.filter_by(email=valid_email).first()
    if not user:
        flash("No account found!", "danger")
        return redirect(request.url)
    if not user.confirmed:
        flash("No account found!", "danger")
        return redirect(request.url)

    if check_password_hash(user.password, data["password"]):
        login_user(user)
        flash(f"Login successful, {user.username}!", "success")
        redirect_to = request.args.get("next")
        if redirect_to:
            print(redirect_to)
            return redirect(redirect_to)
        return redirect(f"{request.url_root}/{app_registry.prefix}")

    flash("Invalid credentials!", "danger")
    return redirect(request.url)


@app_registry.handles("/logout", method="GET")
def logout():
    if current_user.is_anonymous:
        flash("Already logged out!", "danger")
        return redirect(f"{request.url_root}/{app_registry.prefix}")

    logout_user()
    flash(f"Logout successful!", "success")
    return redirect(f"{request.url_root}/{app_registry.prefix}")


@app_registry.handles("/password/change", method="GET")
@login_required
def get_password_change():
    return render_template("change-password.html")


@app_registry.handles("/password/change", method="POST")
@login_required
def post_password_change():
    data = request.form
    print(data["password"])
    if data["password"] != data["confirm_password"]:
        flash("Passwords don't match!", "danger")
        return redirect(request.url)
    print(current_user.username)
    current_user.password = generate_password_hash(
        data.get("password"), "pbkdf2:sha256", 8
    )
    db.session.commit()
    flash("Password change successful!", "success")

    return redirect(f"{request.url_root}/{app_registry.prefix}")


@app_registry.handles("/password/reset", method="GET")
def get_password_reset():
    return render_template("reset-password.html")


@app_registry.handles("/password/reset", method="POST")
def post_password_reset():
    data = request.form

    valid_email, msg = manager.validate_email(data["email"])
    if not valid_email:
        flash(f"{msg}", "danger")
        return redirect(request.url)

    user = User.query.filter_by(email=valid_email).first()
    if not user:
        flash("No account found!", "danger")
        return redirect(request.url)

    user.token = manager.generate_token(expire=manager.valid_hours * 3600)
    db.session.commit()
    mail = manager.create_mail(
        user_mail=valid_email,
        user_id=user.id,
        redirect_url=None,
        task="app/password/change",
        username=user.username,
        token=user.token,
    )
    mail.build_email()
    print(mail.message)
    mail.send_email()
    login_user(user)

    flash(
        "A confirmation email has been sent to your email address. "
        "Please confirm the change to reset your password.",
        "success",
    )

    return redirect(request.url)


@app_registry.handles("/email/change", method="GET")
@login_required
def get_email_change():
    return render_template("change-email.html")


@app_registry.handles("/email/change", method="POST")
@login_required
def post_email_change():
    data = request.form

    if data["email"] != data["confirm_email"]:
        flash("Email addresses don't match!", "danger")
        return redirect(request.url)

    valid_email, msg = manager.validate_email(data["email"], check_deliverability=True)
    if not valid_email:
        flash(f"{msg}", "danger")
        return redirect(request.url)

    user = User.query.filter_by(email=valid_email).first()
    if user:
        flash("Email address already in use!", "danger")
        return redirect(request.url)

    session["pending_email"] = valid_email

    current_user.token = manager.generate_token(expire=manager.valid_hours * 3600)
    db.session.commit()

    mail = manager.create_mail(
        user_mail=valid_email,
        user_id=current_user.id,
        redirect_url=None,
        task="api/email/confirm",
        username=current_user.username,
        token=current_user.token,
    )
    mail.build_email()
    mail.send_email()

    flash(
        "A confirmation email has been sent to your new email address. "
        "Please confirm the change to update your email.",
        "success",
    )
    return redirect(request.url)


@app_registry.handles("/username/change", method="GET")
@login_required
def get_username_change():
    return render_template("change-username.html")


@app_registry.handles("/username/change", method="POST")
@login_required
def post_username_change():
    data = request.form

    valid_username, msg = manager.validate_username(data["username"])
    if not valid_username:
        flash(f"{msg}", "danger")
        return redirect(request.url)

    user = User.query.filter_by(username=valid_username).first()
    if user:
        flash("Username is already in use!", "danger")
        return redirect(request.url)

    current_user.username = valid_username
    db.session.commit()

    flash(f"Username updated to {current_user.username}!", "success")
    return redirect(request.url)


@app_registry.handles("/name/change", method="GET")
@login_required
def get_name_change():
    flash("Changing your display name is not yet possible.", "danger")
    return render_template("change-name.html")


@app_registry.handles("/name/change", method="POST")
@login_required
def post_name_change():
    return redirect(request.url)


@app_registry.handles("/account/delete", method="GET")
@login_required
def get_account_deletion():
    flash("WARNING: Deleting your account is permanent and cannot be undon!", "danger")
    flash("Account deletion is not yet possible.", "danger")
    return render_template("delete-account.html")


@app_registry.handles("/account/delete", method="POST")
@login_required
def post_account_deletion():
    return redirect(request.url)


@app_registry.handles("/archive", method="GET")
@login_required
def get_archive():
    user = User.query.filter_by(id=current_user.id).first()

    # Fetch orders, messages, and logs separately
    air_nomad_profile = AirNomads.query.filter_by(email=user.email).first()
    ressources = Ressources.query.filter_by(user_id=user.id).all()
    movies = TopMovies.query.filter_by(user_id=user.id).all()
    blog_posts = BlogPost.query.filter_by(author_id=user.id).all()
    blog_comments = BlogComment.query.filter_by(author_id=user.id).all()
    # Aggregate into a dictionary
    archive = {
        "user": user.to_dict(),
        "ans": air_nomad_profile.to_dict(),
        "library": [ressource.to_dict() for ressource in ressources],
        "filmhub": [movie.to_dict() for movie in movies],
        "blog": {
            "posts": [post.to_dict() for post in blog_posts],
            "comments": [comment.to_dict() for comment in blog_comments],
        },
    }
    file_path = Path("archive.json")
    with open(file_path, "w") as file:
        json.dump(archive, file, indent=4)

    archive_data = io.BytesIO()
    with open(file_path, "rb") as fo:
        archive_data.write(fo.read())
    # (after writing, cursor will be at last byte, so move it to start)
    archive_data.seek(0)

    os.remove(file_path)

    return send_file(
        archive_data,
        mimetype="application/json",
        download_name="data.json",
        as_attachment=True,
    )


if __name__ == "__main__":
    rebar.init_app(app)
    app.run(debug=True, port=5001)
