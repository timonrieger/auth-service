import os
import dotenv
import time
import secrets
import smtplib
import string

dotenv.load_dotenv()

class Manager:

    def __init__(self, my_mail=os.getenv("GMAIL"), email_password=os.getenv("GMAIL_PWD"), valid_hours=24):
        self.tokens = {}
        self.valid_hours = valid_hours
        self.my_mail = my_mail
        self.email_password = email_password
        

    def generate_token(self, expire):
        """Generate a random token."""
        characters = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(characters) for i in range(20))
        if expire:
            self.tokens[token] = time.time()
        return token
        

    def check_token(self, token):
        """Check if a token is valid within the specified time."""
        if token in self.tokens:
            creation_time = self.tokens[token]
            current_time = time.time()
            if current_time - creation_time <= self.valid_hours * 3600:
                return True
            else:
                del self.tokens[token]
            return False
        return False
    
    
    def delete_token(self, token):
        """Delete a token from the dictionary."""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False
    
    def create_mail(self, user_mail, user_id, redirect_url, task, username=""):
        """Create a Mail instance with user information."""
        return self.Mail(self, user_mail, user_id, redirect_url, task, username)


    class Mail:
        
        def __init__(self, manager, user_mail, user_id, redirect_url, task, username=""):
            self.user_mail = user_mail
            self.user_id = user_id
            self.redirect_url = redirect_url
            self.username = username
            self.task = task
            self.message = ""
            self.link = ""
            self.token = ""
            self.manager = manager
            

        def build_link(self):
            """Build a link with the token."""
            return f"https://auth.timonrieger.de/{self.task}?id={self.user_id}&token={self.token}&then={self.redirect_url}"
        
        
        def build_account_confirmation_message(self):
            """Build the account confirmation message."""
            return (f"Subject: Account Confirmation Link\n\n"
                    f"Hello {self.username},\n\n"
                    f"Thank you for signing up! You can now use your credentials across any of my projects that support accounts."
                    f"To complete your registration, please click the link below within the next {self.manager.valid_hours} hours:\n\n"
                    f"{self.link}\n\n"
                    f"If you forgot clicking the link, register again.\n\n"
                    f"If you did not request this registration or have any questions, please ignore this message.\n\n"
                    f"Best regards,\n\nTimon Rieger\nhttps://timonrieger.de")
            
            
        def build_password_reset_message(self):
            """Build the password reset message."""
            return (f"Subject: Password Reset Request\n\n"
                    f"Hello {self.username},\n\n"
                    f"To complete the process of resetting your password, please click the link below within the next {self.manager.valid_hours} hours:\n\n"
                    f"{self.link}\n\n"
                    f"If you did not request a password reset, please ignore this message, and your account will remain secure.\n\n"
                    f"Best regards,\n\nTimon Rieger\nhttps://timonrieger.de")


        def build_email(self):
            """Build the email based on the task type."""
            self.token = self.manager.generate_token(expire=True)
            self.link = self.build_link()
            if self.task == "confirm":
                self.message = self.build_account_confirmation_message()
            elif self.task == "reset":
                self.message = self.build_password_reset_message()
            return True
        
        
        def send_email(self):
            """Send the email message using SMTP."""
            with smtplib.SMTP("smtp.gmail.com", port=587) as server:
                server.starttls()
                server.login(self.manager.my_mail, self.manager.email_password)
                server.sendmail(self.manager.my_mail, self.user_mail, self.message)
            return True
