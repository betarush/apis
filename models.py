from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import *
import os

db_host = str(os.getenv("DB_HOST"))
user = str(os.getenv("USER"))
password = str(os.getenv("PASS"))
db_name = str(os.getenv("DB"))
mysql_str = 'mysql+pymysql://geottuse:G3ottu53?@localhost/getproductfeedback'

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
	password = db.Column(db.String(170), unique=True)
	username = db.Column(db.String(25), unique=True)
	earnings = db.Column(db.Float())
	bankaccountInfo = db.Column(db.String(220))
	tokens = db.Column(db.String(75), unique=True)
	firstTime = db.Column(db.Boolean)
	isBanned = db.Column(db.Boolean)

	def __init__(self, email, password, username, earnings, bankaccountInfo, tokens, firstTime, isBanned):
		self.email = email
		self.password = password
		self.username = username
		self.earnings = earnings
		self.bankaccountInfo = bankaccountInfo
		self.tokens = tokens
		self.firstTime = firstTime
		self.isBanned = isBanned

class Product(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50))
	image = db.Column(db.String(75))
	info = db.Column(db.String(100))
	link = db.Column(db.String(50))
	creatorId = db.Column(db.Integer)
	otherInfo = db.Column(db.String(85))
	amountLeftover = db.Column(db.Float)
	amountSpent = db.Column(db.Float)
	deposited = db.Column(db.Integer)

	def __init__(self, name, image, info, link, creatorId, otherInfo, amountLeftover, amountSpent, deposited):
		self.name = name
		self.image = image
		self.info = info
		self.link = link
		self.creatorId = creatorId
		self.otherInfo = otherInfo
		self.amountLeftover = amountLeftover
		self.amountSpent = amountSpent
		self.deposited = deposited

class ProductTesting(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	testerId = db.Column(db.Integer)
	productId = db.Column(db.Integer)
	advice = db.Column(db.String(500))
	created = db.Column(db.Integer)
	withdrawned = db.Column(db.Boolean)

	def __init__(self, testerId, productId, advice, created, withdrawned):
		self.testerId = testerId
		self.productId = productId
		self.advice = advice
		self.created = created
		self.withdrawned = withdrawned

class TesterRate(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	productId = db.Column(db.Integer)
	testerId = db.Column(db.Integer)
	testingId = db.Column(db.Integer)
	type = db.Column(db.String(10))
	reason = db.Column(db.String(100))
	advice = db.Column(db.String(500))
	created = db.Column(db.Integer)

	def __init__(self, productId, testerId, testingId, type, reason, advice, created):
		self.productId = productId
		self.testerId = testerId
		self.testingId = testingId
		self.type = type
		self.reason = reason
		self.advice = advice
		self.created = created

class PendingPayout(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	accountId = db.Column(db.String(25))
	transferGroup = db.Column(db.String(25))
	amount = db.Column(db.Float())
	email = db.Column(db.String(50))
	created = db.Column(db.Integer)

	def __init__(self, accountId, transferGroup, amount, email, created):
		self.accountId = accountId
		self.transferGroup = transferGroup
		self.amount = amount
		self.email = email
		self.created = created