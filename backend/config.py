import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'casa-system-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "casa.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'casa-jwt-secret-2026')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours

    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-ccfdad4f460c44bdbf1ab6ff6af16091')
    DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
    DEEPSEEK_MODEL = 'deepseek-chat'
