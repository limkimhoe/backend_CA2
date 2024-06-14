import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    # Example MySQL connection string
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://user:password@http://localhost:3306/mydatabase'
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:example@dbMySQL:3306/mydatabase2'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:example@dbMySQL:3306/mydatabase'
    
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://kimhoe.gcit:P06coqOWytAT@ep-little-hall-a1ykg9bf.ap-southeast-1.aws.neon.tech/usmdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'a_default_jwt_secret_key'

    UPLOAD_FOLDER = 'static/images/'  # Directory where images will be stored
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max-limit for uploads

    

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = 'postgresql://kimhoe.gcit:P06coqOWytAT@ep-little-hall-a1ykg9bf.ap-southeast-1.aws.neon.tech/usmdb'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@dbMySQL:3306/mydatabase2'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
