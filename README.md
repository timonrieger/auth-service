# Centralized Authentication Service

This project is a Flask-based centralized authentication service that provides user registration, login, and email confirmation functionalities. It uses the [`database-service`](https://github.com/timonrieger/database-service.git) as database schema.

## Features

- User registration with email confirmation
- User login with password hashing
- Email token generation and validation for account confirmation

## Requirements

- Python 3.x
- Flask
- Flask-SQLAlchemy
- Werkzeug
- python-dotenv

## Setup

1. Clone the repository:
	```sh
	git clone https://github.com/timonrieger/auth-service.git
	cd auth-service
	```

2. Create a virtual environment and activate it:
	```sh
	python -m venv venv
	source venv/bin/activate  # On Windows use `venv\Scripts\activate`
	```

3. Install the required packages:
	```sh
	pip install -r requirements.txt
	```

4. Create a `.env` file in the root directory and add your configuration:
	```env
	SECRET=your_secret_key
	DB_URI=your_database_uri
	```

5. Run the application:
	```sh
	python main.py
	```

## Endpoints

- `GET /` - Home endpoint to check if the service is operating.
- `POST /register` - Endpoint to register a new user.
- `POST /login` - Endpoint to login an existing user.
- `GET /confirm` - Endpoint to confirm a user's email.

## Usage

### Register a new user

Send a POST request to `/register` with the following parameters:
- `email`
- `password`
- `username`
- `then` (URL to redirect after confirmation)

### Login

Send a POST request to `/login` with the following parameters:
- `email`
- `password`

### Confirm Email

Send a GET request to `/confirm` with the following parameters:
- `id` (user ID)
- `token` (confirmation token)
- `then` (redirect URL to include in the confirmation email)

You might want to change the email content in `utils.py`

## License

This project is licensed under the MIT License.