import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '...'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'postgresql://admin:123456er@localhost/statix'
    SQLALCHEMY_TRACK_MODIFICATIONS = False