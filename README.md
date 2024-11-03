# Private Auth Service

    •	Each of your apps should have a login form that collects user credentials and sends them to the central Auth Service’s /login endpoint.
	•	Store the returned JWT token in the client (e.g., in a browser’s localStorage or sessionStorage).
	•	Use the /validate-token endpoint to validate the JWT for protected routes.

## Register

```bash
curl -X POST http://127.0.0.1:5000/register \
-H "Content-Type: application/json" \
-d '{"email": "testuser@example.com", "password": "mypassword"}'
```

## Login

```bash
curl -X POST http://127.0.0.1:5000/login \
-H "Content-Type: application/json" \
-d '{"email": "testuser@example.com", "password": "mypassword"}'
```

## Validate Token

```bash
curl -X POST http://127.0.0.1:5000/validate-token \
-H "Content-Type: application/json" \
-d '{"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VyX2VtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20ifQ.djxyDo5Unsaj8d9luBY5y1WN-v8Fr6HD6NO-G5ULbMw"}'
```