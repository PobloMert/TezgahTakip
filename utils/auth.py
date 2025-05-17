import hashlib
import binascii
import os
from datetime import datetime, timedelta
import jwt
from PyQt5.QtWidgets import QMessageBox

class AuthManager:
    def __init__(self, secret_key):
        self.secret_key = secret_key
        
    def hash_password(self, password):
        """Şifreyi güvenli şekilde hash'le"""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                    salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii')
    
    def verify_password(self, stored_password, provided_password):
        """Hash'lenmiş şifreyi doğrula"""
        salt = stored_password[:64]
        stored_password = stored_password[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                    provided_password.encode('utf-8'), 
                                    salt.encode('ascii'), 
                                    100000)
        pwdhash = binascii.hexlify(pwdhash).decode('ascii')
        return pwdhash == stored_password
    
    def create_token(self, user_id, expires_days=30):
        """JWT token oluştur"""
        payload = {
            'exp': datetime.utcnow() + timedelta(days=expires_days),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        """JWT token doğrula"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            QMessageBox.warning(None, 'Hata', 'Oturum süresi doldu')
            return None
        except jwt.InvalidTokenError:
            QMessageBox.warning(None, 'Hata', 'Geçersiz token')
            return None
