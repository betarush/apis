from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import *
import os

db_host = str(os.getenv("DB_HOST"))
user = str(os.getenv("USER"))
password = str(os.getenv("PASS"))
db_name = str(os.getenv("DB"))
mysql_str = 'mysql://geottuse:G3ottu53?@localhost/getproductfeedback'

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
	paymentInfo = db.Column(db.String(100))
	bankaccountInfo = db.Column(db.String(200))
	tokens = db.Column(db.String(75), unique=True)

	def __init__(self, email, password, username, earnings, paymentInfo, bankaccountInfo, tokens):
		self.email = email
		self.password = password
		self.username = username
		self.earnings = earnings
		self.paymentInfo = paymentInfo
		self.bankaccountInfo = bankaccountInfo
		self.tokens = tokens

class Product(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20))
	image = db.Column(db.String(75))
	info = db.Column(db.String(100))
	link = db.Column(db.String(50))
	creatorId = db.Column(db.Integer)
	otherInfo = db.Column(db.String(85), unique=True)
	amount = db.Column(db.Float)

	def __init__(self, name, image, info, link, creatorId, otherInfo, amount):
		self.name = name
		self.image = image
		self.info = info
		self.link = link
		self.creatorId = creatorId
		self.otherInfo = otherInfo
		self.amount = amount

class ProductTesting(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	testerId = db.Column(db.Integer)
	productId = db.Column(db.Integer)
	feedback = db.Column(db.String(100))
	earned = db.Column(db.Boolean)
	rejectedReason = db.Column(db.String(200))

	def __init__(self, testerId, productId, feedback, earned, rejectedReason):
		self.testerId = testerId
		self.productId = productId
		self.feedback = feedback
		self.earned = earned
		self.rejectedReason = rejectedReason
