import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))


def _get_database():
    host = os.environ.get('DATABASE_HOST')
    user = os.environ.get('DATABASE_USER')
    password = os.environ.get('DATABASE_PASSWORD')
    database = os.environ.get('DATABASE_NAME')
    return "mysql+pymysql://{}:{}@{}/{}".format(user,password,host,database)


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    CORS_HEADERS = 'Content-Type'
    DATA_PER_PAGE = 7
    PDF_FOLDER = basedir + '/app/static/pdfs/'
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USERNAME = "rmontemayor0101@gmail.com"
    MAIL_PASSWORD = "xusxeecqychjduvv"
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

class DevelopmentConfig(Config):
    """
    Development configurations
    """

    SQLALCHEMY_DATABASE_URI = _get_database()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    # SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """
    Production configurations
    """
    SQLALCHEMY_DATABASE_URI = _get_database()
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class TestingConfig(Config):
    """
    Testing configurations
    """

    TESTING = True
    # SQLALCHEMY_ECHO = True


app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}


class HomeBestConfig:
    load_dotenv()
    HOST = os.environ.get('DATABASE_HOST')
    USER = os.environ.get('DATABASE_USER')
    PASSWORD = os.environ.get('DATABASE_PASSWORD')
    DATABASE = os.environ.get('DATABASE_NAME')
