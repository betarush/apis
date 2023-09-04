from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import *
import os

db_host = str(os.getenv("DB_HOST"))
user = str(os.getenv("USER"))
password = str(os.getenv("PASS"))
db_name = str(os.getenv("DB"))
mysql_str = 'mysql://geottuse:G3ottu53?@localhost/chatee'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = mysql_str
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['MYSQL_HOST'] = db_host
app.config['MYSQL_USER'] = user
app.config['MYSQL_PASSWORD'] = password
app.config['MYSQL_DB'] = db_name

db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(50))
	password = db.Column(db.String(110), unique=True)
	username = db.Column(db.String(25), unique=True)
	earnings = db.Column(db.Float())

	def __init__(self, email, password, username, earnings):
		self.email = email
		self.password = password
		self.username = username
		self.earnings = earnings

class Product(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20))
	image = db.Column(db.String(75))
	info = db.Column(db.String(100))
	link = db.Column(db.String(50))
	creatorId = db.Column(db.Integer)

	def __init__(self, name, image, info, link, creatorId):
		self.name = name
		self.image = image
		self.info = info
		self.link = link
		self.creatorId = creatorId

class ProductTesting(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	testerId = db.Column(db.Integer)
	productId = db.Column(db.Integer)
	feedback = db.Column(db.String(100))

	def __init__(self, testerId, productId, feedback):
		self.testerId = testerId
		self.productId = productId
		self.feedback = feedback
