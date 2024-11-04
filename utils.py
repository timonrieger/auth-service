import secrets, string, smtplib, time

class MailManager():

    def __init__(self):
        self.tokens = {}
        self.valid_hours = 24

    def generate_token(self, expire):
        characters = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(characters) for i in range(20))
        if expire:
            self.tokens[token] = time.time()
        return token

    def send_email(self, user_mail, message, my_mail="timonriegerx@gmail.com", email_password="xqfx nyzr nojx bukb"):
        try:
            with smtplib.SMTP("smtp.gmail.com", port=587) as server:
                server.starttls()
                server.login(my_mail, email_password)
                server.sendmail(my_mail, user_mail, message)
            return True
        except Exception:
            return False

    def check_token(self, token):
        """Check if a token is valid within the specified time."""
        if token in self.tokens:
            creation_time = self.tokens[token]
            current_time = time.time()
            # Check if token was created within the valid time
            if current_time - creation_time <= self.valid_hours * 3600:
                return True
            else:
                del self.tokens[token]
            return False
        return False


    def build_email(self, redirect_url, user_mail, user_id, username=""):
        """Send a confirmation link to the specified email."""
        token = self.generate_token(expire=True)
        confirmation_link = f"https://auth.timonrieger.de/confirm?id={user_id}&token={token}&then={redirect_url}"
        message = (f"Subject: Account Confirmation Link\n\n"
                   f"Hello {username},\n\n"
                   f"Thank you for signing up! To complete your registration, please click the link below within the next {self.valid_hours} hours:\n\n"
                   f"{confirmation_link}\n\n"
                   f"If you did not request this registration or have any questions, please ignore this message.\n\n"
                   f"Best regards,\n\nTimon Rieger")
        return self.send_email(user_mail, message)
