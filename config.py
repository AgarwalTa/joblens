import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "joblens-dev-secret")
    DATABASE = os.path.join(BASE_DIR, "data", "joblens.db")
    DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
