# Centralized Authentication Service

This project is a Flask-based centralized authentication service that provides user registration, login, and email confirmation functionalities. It uses the [`database-service`](https://github.com/timonrieger/database-service.git) as database schema.

## Features

- User registration with email confirmation
- User login with password hashing
- Email token generation and validation for account confirmation
- Email and password changes
- Password reset management
- Redirect URLs for seamless UX
- API Key management (creation and verification)
- User management frontend to give the user full control about his account

## Limitations

- No user account deletion
- No data export per user 

## Requirements

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

4. Create a `.env` file in the root directory and add your configuration settings. Use the database URL provided by your hosting service. Ensure the connection string matches the one used in the database:
	```env
	SECRET_KEY=your_secret_key
	DB_URI=your_database_uri
	```

5. Run the application:
	```sh
	python3 -m main
	```

## Usage

### Register a new user

Send a POST request to `/register` with the following parameters:
- `email`
- `password`
- `username`
- `then` (URL to redirect after account confirmation)

```python
data = {"email": email, "password": password, "username": username, "then": "https://YOURDOMAIN/login"
}
response = requests.post(f"{AUTH_URL}/register", json=data)
```

### Login

Send a POST request to `/login` with the following parameters:
- `email`
- `password`

```python
data = {"email": email, "password": password}
response = requests.post(url=AUTH_URL, json=data)
```


### Create API Key

Send a POST request to `/apikey/create` with the following parameters:
- `id` (user ID)

```python
data = {"id": id}
response = requests.post(url=f"{AUTH_URL}/apikey/create", json=data)
```

### Verify API Key

Send a GET request to `/apikey/verify` with the authorization header:
- `Authorization` (no Bearer prefix)

```python
headers = {'Authorization': token}
response = requests.get(url=f"{AUTH_URL}/apikey/verify", headers=headers)
```

### Response

Returns status code 200 on success. Anything else is considered to be an error. The response also always contains a message.
```python
response.status_code
response.json()['message']
```

### Example

Your code might look like this for logging a user in (using flask and flask_login):
```python
response = requests.post(url=f"{AUTH_URL}/login", json=data)
if response.status_code == 200:
		flash(response.json()['message'], "success")
		login_user(user)
		return redirect(url_for("home"))
flash(response.json()['message'], "error")
```

## Configuration

You will have to change the email content in `utils.py` by updating the urls and my name. You can update anything else as well.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.