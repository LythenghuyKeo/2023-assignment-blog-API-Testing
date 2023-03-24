from flask import Flask
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
app=Flask(__name__)
app.config['SECRET_KEY']="28c52d893e7d3fd4329ebd3ad2f7cbd5"
app.config['SQLALCHEMY_DATABASE_URI']="postgresql://postgres:keochanny$1@localhost:5432/testing_2"
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# client = MongoClient('localhost', 27017)
# mongo_database_name="2023_KIT_KPMS_Training_P1_Assignment_School"
# db =client[mongo_database_name]
from flaskAssignment import route