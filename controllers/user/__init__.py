from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message

cors = CORS(app)

@app.route("/welcome_user")
def welcome_user():
	return "startupfeedback: Welcome to user"

@app.route("/register", methods=["POST"])
def register():
	content = request.get_json()

	email = content['email']
	password = content['password']
	username = "user" + getId()

	bankaccountInfo = json.dumps({"line1": "", "zipcode": "", "dob": {"day": 0, "month": 0, "year": 0}, "firstName": "", "lastName": ""})

	creator = stripe.Customer.create(
		description="Product creator: " + username,
		email=email
	)

	tokens = json.dumps({ "creator": creator.id, "account": "" })

	userId = query("insert into user (email, password, username, earnings, bankaccountInfo, tokens) values ('" + email + "', '" + generate_password_hash(password) + "', '" + username + "', 0.0, '" + bankaccountInfo + "', '" + tokens + "')", True).lastrowid

	return { "id": userId }

@app.route("/login", methods=["POST"])
def login():
	content = request.get_json()

	email = content['email']
	password = content['password']

	customer = query("select id, password from user where email = '" + email + "'", True).fetchone()

	if customer != None:
		if check_password_hash(customer["password"], password):
			return { "id": customer["id"] }

	return { "status": "noExist" }, 400

@app.route("/get_user_info", methods=["POST"])
def get_user_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select email, tokens from user where id = " + userId, True).fetchone()

	if user != None:
		username = user["email"].split("@")[0]
		tokens = json.loads(user["tokens"])

		if tokens["creator"] != "":
			paymentMethod = stripe.Customer.retrieve(tokens["creator"])
			paymentMethod = paymentMethod.default_source != None
		else:
			paymentMethod = False

		if tokens["account"] != "":
			account = stripe.Account.retrieve(tokens["account"])
			account = len(account.external_accounts.data) > 0
		else:
			account = False

		earnings = query("select count(*) as num from product_testing where testerId = " + userId + " and earned = 1", True).fetchone()["num"]
		rejectedReasons = query("select count(*) as num from product_testing where testerId = " + userId + " and not rejectedReason = ''", True).fetchone()["num"]

		return {
			"username": username,
			"earnings": round(earnings * (launchAmount / 5), 2),
			"rejectedReasons": rejectedReasons,
			"paymentDone": paymentMethod,
			"bankaccountDone": account
		}

	return { "status": "nonExist" }, 400

@app.route("/get_payment_info", methods=["POST"])
def get_payment_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select tokens from user where id = " + userId, True).fetchone()

	if user != None:
		tokens = json.loads(user["tokens"])

		customer = stripe.Customer.retrieve(tokens["creator"])
		card = None

		if customer.default_source != None:
			card = stripe.Customer.retrieve_source(
				tokens["creator"],
				customer.default_source
			)
			card = {
				"name": card.brand,
				"last4": card.last4
			}

			# MasterCard, American Express, Discover, Diners Club, JCB, UnionPay

		return { "card": card }

	return { "status": "nonExist" }, 400

@app.route("/get_bankaccount_info", methods=["POST"])
def get_bankaccount_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select tokens from user where id = " + userId, True).fetchone()

	if user != None:
		tokens = json.loads(user["tokens"])
		account = None

		if tokens["account"] != "":
			account = stripe.Account.retrieve(tokens["account"])
			account = account.external_accounts.data[0]
			account = {
				"name": account.bank_name,
				"last4": account.last4
			}

		return { "bank": account }

	return { "status": "nonExist" }, 400

@app.route("/submit_payment_info", methods=["POST"])
def submit_payment_info():
	content = request.get_json()

	userId = str(content['userId'])
	token = content['token']

	user = query("select id, tokens from user where id = " + userId, True).fetchone()

	if user != None:
		tokens = json.loads(user["tokens"])
		customer = stripe.Customer.list_sources(tokens["creator"], object="card", limit=1)

		if len(customer.data) == 0:
			stripe.Customer.create_source(
				tokens["creator"],
				source=token
			)
		else:
			stripe.Customer.modify(
				tokens["creator"],
				source=token
			)

		return { "msg": "" }

	return { "status": "nonExist" }, 400

@app.route("/submit_bankaccount_info", methods=["POST"])
def submit_bankaccount_info():
	content = request.get_json()

	userId = str(content['userId'])
	line1 = content['line1']
	zipcode = content['zipcode']
	dob = content['dob']
	firstName = content['firstName']
	lastName = content['lastName']
	country = content['country']
	token = content['token']

	user = query("select id, email, tokens, bankaccountInfo from user where id = " + userId, True).fetchone()

	if user != None:
		tokens = json.loads(user["tokens"])
		bankaccountInfo = json.loads(user["bankaccountInfo"])

		bankaccountInfo["line1"] = line1
		bankaccountInfo["zipcode"] = zipcode
		bankaccountInfo["dob"] = dob
		bankaccountInfo["firstName"] = firstName
		bankaccountInfo["lastName"] = lastName
		bankaccountInfo["country"] = country
		bankaccountInfo["line1"] = line1

		if tokens["account"] == "":
			day = dob[2:4]
			month = dob[:2]
			year = dob[4:8]

			account = stripe.Account.create(
				type="custom",
				country=country,
				email=user["email"],
				capabilities={
			    "card_payments": {"requested": True},
			    "transfers": {"requested": True},
			  },
			  business_type="individual",
			  individual={
			  	"address": { 
			  		"line1": line1,
			  		"postal_code": zipcode 
			  	},
			  	"dob": {
			  		"day": int(day),
			  		"month": int(month),
			  		"year": int(year)
			  	},
			  	"first_name": firstName,
			  	"last_name": lastName
			  },
			  external_account=token,
			  tos_acceptance={"date": int(time()), "ip": "8.8.8.8"}
			)

			tokens["account"] = account.id

		query("update user set bankaccountInfo = '" + json.dumps(bankaccountInfo) + "', tokens = '" + json.dumps(tokens) + "' where id = " + userId)

		return { "msg": "" }

	return { "status": "nonExist" }, 400

@app.route("/get_earnings", methods=["POST"])
def get_earnings():
	content = request.get_json()

	userId = str(content['userId'])

	tester = query("select email, tokens from user where id = " + userId, True).fetchone()
	tokens = json.loads(tester["tokens"])

	earnings = query("select id, productId from product_testing where testerId = " + userId + " and earned = 1", True).fetchall()
	earnedAmount = 0.0

	for info in earnings:
		product = query("select name, otherInfo from product where id = " + str(info["productId"]), True).fetchone()
		otherInfo = json.loads(product["otherInfo"])
		charge = otherInfo["charge"]
		transferGroup = otherInfo["transferGroup"]
		amount = launchAmount / 5

		stripe.Transfer.create(
			amount=int(amount * 100),
			currency="cad",
			description="Rewarded $" + str(round(amount, 2)) + " to tester: " + tester["email"] + " of product: " + product["name"],
			destination=tokens["account"],
			source_transaction=charge,
			transfer_group=transferGroup
		)

		earnedAmount += amount

		query("delete from product_testing where id = " + str(info["id"]))

	return { "earnedAmount": earnedAmount }

@app.route("/reward_customer", methods=["POST"])
def reward_customer():
	content = request.get_json()

	productId = str(content['productId'])
	testerId = str(content['testerId'])

	product = query("select amount from product where id = " + productId, True).fetchone()
	amount = float(product["amount"]) - (launchAmount / 5)

	query("update product set amount = " + str(round(amount, 2)) + " where id = " + productId)
	query("update product_testing set earned = 1 where productId = " + productId + " and testerId = " + testerId)

	return { "msg": "" }

@app.route("/reject_feedback", methods=["POST"])
def reject_feedback():
	content = request.get_json()

	productId = str(content['productId'])
	testerId = str(content['testerId'])
	reason = content['reason']

	query("update product_testing set rejectedReason = '" + reason + "' where productId = " + productId + " and testerId = " + testerId)

	return { "msg": "" }

