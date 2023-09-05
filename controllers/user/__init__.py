from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message

cors = CORS(app)

# card token: tok_1Nmi4sFqjgkiO0WHePwI3WCk
# customer token: cus_OZWKZkfijAH65g
# account token: acct_1NmA1PFqjgkiO0WH

@app.route("/welcome_user")
def welcome_user():
	return "startupfeedback: Welcome to user"

@app.route("/register", methods=["POST"])
def register():
	content = request.get_json()

	email = content['email']
	password = content['password']
	username = "user" + getId()

	paymentInfo = json.dumps({ "name": "", "number": "", "cvc": "", "expdate": "" })
	bankaccountInfo = json.dumps({"line1": "", "zipcode": "", "dob": {"day": 0, "month": 0, "year": 0}, "firstName": "", "lastName": ""})

	creator = stripe.Customer.create(
		description="Product creator: " + username,
		email=email
	)

	tokens = json.dumps({ "creator": creator.id, "account": "" })

	userId = query("insert into user (email, password, username, earnings, paymentInfo, bankaccountInfo, tokens) values ('" + email + "', '" + generate_password_hash(password) + "', '" + username + "', 0.0, '" + paymentInfo + "', '" + bankaccountInfo + "', '" + tokens + "')", True).lastrowid

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

		earnings = query("select count(*) from product_testing where testerId = " + userId + " and earned = 1", True).fetchone()["count(*)"]

		return {
			"username": username,
			"earnings": round(earnings, 2),
			"paymentDone": paymentMethod,
			"bankaccountDone": account
		}

	return { "status": "nonExist" }, 400

@app.route("/get_payment_info", methods=["POST"])
def get_payment_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select paymentInfo from user where id = " + userId, True).fetchone()

	if user != None:
		paymentInfo = json.loads(user["paymentInfo"])

		return paymentInfo

	return { "status": "nonExist" }, 400

@app.route("/get_bankaccount_info", methods=["POST"])
def get_bankaccount_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select bankaccountInfo from user where id = " + userId, True).fetchone()

	if user != None:
		bankaccountInfo = json.loads(user["bankaccountInfo"])

		return bankaccountInfo

	return { "status": "nonExist" }, 400

@app.route("/submit_payment_info", methods=["POST"])
def submit_payment_info():
	content = request.get_json()

	userId = str(content['userId'])
	name = content['name']
	number = content['number']
	cvc = content['cvc']
	expdate = content['expdate']

	user = query("select id, tokens, paymentInfo from user where id = " + userId, True).fetchone()

	if user != None:
		tokens = json.loads(user["tokens"])
		paymentInfo = json.loads(user["paymentInfo"])

		paymentInfo["name"] = name
		paymentInfo["number"] = number
		paymentInfo["cvc"] = cvc
		paymentInfo["expdate"] = expdate

		customer = stripe.Customer.list_sources(tokens["creator"], object="card", limit=1)
		# card = stripe.Token.create(
		# 	card={
		# 		"number": number,
		# 		"exp_month": int(expdate[:2]),
		# 		"exp_year": int(expdate[2:6]),
		# 		"cvc": cvc
		# 	}
		# )
		card = "tok_bypassPending"

		if len(customer.data) == 0:
			stripe.Customer.create_source(
				tokens["creator"],
				source=card
			)
		else:
			stripe.Customer.modify(
				tokens["creator"],
				source=card
			)

			print(tokens["creator"])

		query("update user set paymentInfo = '" + json.dumps(paymentInfo) + "' where id = " + userId)

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
	currency = content['currency']
	routingNumber = content['routingNumber']
	accountNumber = content['accountNumber']

	user = query("select id, email, tokens, bankaccountInfo from user where id = " + userId, True).fetchone()

	if user != None:
		tokens = json.loads(user["tokens"])

		if tokens["account"] == "":
			bankaccountInfo = json.loads(user["bankaccountInfo"])

			bankaccountInfo["line1"] = line1
			bankaccountInfo["zipcode"] = zipcode
			bankaccountInfo["dob"] = dob
			bankaccountInfo["firstName"] = firstName
			bankaccountInfo["lastName"] = lastName
			bankaccountInfo["country"] = country
			bankaccountInfo["routingNumber"] = routingNumber
			bankaccountInfo["accountNumber"] = accountNumber
			bankaccountInfo["line1"] = line1

			# token = stripe.Token.create(
			# 	bank_account={
			# 		"country": country,
			# 		"currency": currency,
			# 		"account_holder_name": firstName + " " + lastName,
			# 		"account_holder_type": "individual",
			# 		"routing_number": routingNumber,
			# 		"account_number": accountNumber
			# 	}
			# )

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
			  external_account="btok_us_verified",
			  tos_acceptance={"date": int(time()), "ip": "8.8.8.8"},
			  settings={
			  	"payouts": { 
			  		"schedule": {"interval": "manual"}
			  	}
			  }
			)

			tokens["account"] = account.id

		query("update user set bankaccountInfo = '" + json.dumps(bankaccountInfo) + "', tokens = '" + json.dumps(tokens) + "' where id = " + userId)

		return { "msg": "" }

	return { "status": "nonExist" }, 400

@app.route("/reward_customer", methods=["POST"])
def reward_customer():
	content = request.get_json()

	productId = str(content['productId'])
	testerId = str(content['testerId'])

	tester = query("select email, tokens from user where id = " + testerId, True).fetchone()
	product = query("select name, otherInfo from product where id = " + str(productId), True).fetchone()
	otherInfo = json.loads(product["otherInfo"])
	tokens = json.loads(tester["tokens"])
	charge = otherInfo["charge"]
	transferGroup = otherInfo["transferGroup"]

	amount = 2.00
	# stripe.Transfer.create(
	# 	amount=int(amount * 100),
	# 	currency="cad",
	# 	description="Rewarded $2.00 to tester: " + tester["email"] + " of product: " + product["name"],
	# 	destination=tokens["account"],
	# 	source_transaction=charge,
	# 	transfer_group=transferGroup
	# )

	query("update product_testing set earned = 1 where productId = " + productId + " and testerId = " + testerId)

	return { "msg": "" }

