from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message
import os, requests

app.config['MAIL_SERVER']='smtp.zoho.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'admin@geottuse.com'
app.config['MAIL_PASSWORD'] = 'q0rtghsdui!Fwug'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

cors = CORS(app)
mail = Mail(app)

@app.route("/welcome_user")
def welcome_user():
	return "betarush: Welcome to user"

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

	tokens = json.dumps({ "customer": creator.id, "account": "" })

	password = generate_password_hash(password)

	userId = query("insert into user (email, password, username, earnings, bankaccountInfo, tokens, firstTime, isBanned) values ('" + email + "', '" + password + "', '" + username + "', 0.0, '" + bankaccountInfo + "', '" + tokens + "', 1, 0)", True).lastrowid

	return { "id": userId }

@app.route("/login", methods=["POST"])
def login():
	content = request.get_json()

	email = content['email']
	password = content['password']

	user = query("select id, password, firstTime from user where email = '" + email + "'", True).fetchone()

	if user != None:
		if check_password_hash(user["password"], password):
			return { "id": user["id"], "firstTime": user["firstTime"] }
		else:
			return { "status": "passwordWrong" }, 400

	return { "status": "nonExist" }, 400

@app.route("/verify", methods=["POST"])
def verify():
	content = request.get_json()

	email = content['email']

	user = query("select id from user where email = '" + email + "'", True).fetchone()

	if user == None:
		verifyCode = ""

		for n in range(4):
			verifyCode += str(randint(0, 9))

		# email sent properly
		html = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	"
		html += "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: rgba(0, 0, 0, 0.5); }</style></head><body>	"
		html += "<div style='background-color: #efefef; border-radius: 10px; display: flex; flex-direction: column; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
		html += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div><h3 style='color: grey; text-align: center;'>BetaRush</h3>		</div>		"
		html += "<div style='color: black; font-size: 25px; font-weight: bold; margin: 0 10%; text-align: center;'>			"
		html += "Your verification code is " + verifyCode
		html += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
		html += "</div>	</div></body></html>"

		send_email(email, "BetaRush Verification Code", html)

		return { "verifycode": verifyCode }

	return { "status": "exist" }, 400

@app.route("/get_user_info", methods=["POST"])
def get_user_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select email, tokens, firstTime, isBanned from user where id = " + userId, True).fetchone()

	if user != None:
		sql = "select count(*) as num from product_testing where not advice = '' and productId in (select id from product where creatorId = " + userId + ") and ("
		sql += "select count(*) from tester_rate where testerId = product_testing.testerId and productId = product_testing.productId"
		sql += ") = 0"
		numAdvices = query(sql, True).fetchone()["num"]

		username = user["email"].split("@")[0]
		tokens = json.loads(user["tokens"])

		if tokens["customer"] != "":
			paymentMethod = stripe.Customer.list_payment_methods(
			  tokens["customer"],
			  type="card",
			)

			if len(paymentMethod.data) > 0:
				paymentMethod = {
					"brand": paymentMethod.data[0].card.brand,
					"last4": paymentMethod.data[0].card.last4
				}
			else:
				paymentMethod = { "brand": "", "last4": "" }
		else:
			paymentMethod = { "brand": "", "last4": "" }

		if tokens["account"] != "":
			account = stripe.Account.retrieve(tokens["account"])
			account = len(account.external_accounts.data) > 0
		else:
			account = False

		numCreatedProducts = query("select count(*) as num from product where creatorId = " + userId, True).fetchone()["num"]
		amountEarned = query("select sum(amountSpent / 5) as earnings from product where id in (select productId from product_testing where testerId = " + userId + ") and not json_extract(otherInfo, '$.charge') = ''", True).fetchone()
		
		sql = "select count(*) * 2 as num from product_testing where (select count(*) from product where id = product_testing.productId and json_extract(otherInfo, '$.charge') = '') > 0"
		amountPending = query(sql, True).fetchone()["num"]
		earnings = 0

		if amountEarned["earnings"] != None:
			earnings = round(amountEarned["earnings"], 2)

		return {
			"username": username,
			"earnings": earnings,
			"numAdvices": numAdvices,
			"paymentDone": paymentMethod,
			"amountPending": amountPending,
			"bankaccountDone": account,
			"firstTime": user["firstTime"],
			"isCreator": numCreatedProducts > 0,
			"banned": user["isBanned"] == 1
		}

	return { "status": "nonExist" }, 400

@app.route("/get_ratings_num", methods=["POST"])
def get_ratings_num():
	content = request.get_json()

	userId = str(content['userId'])

	return { 
		"ratings": {
			"numWarns": query("select count(*) as num from tester_rate where testerId = " + userId + " and type = 'warn'", True).fetchone()["num"],
			"numGoods": query("select count(*) as num from tester_rate where testerId = " + userId + " and type = 'good'", True).fetchone()["num"],
			"numNice": query("select count(*) as num from tester_rate where testerId = " + userId + " and type = 'nice'", True).fetchone()["num"]
		}
	}

@app.route("/get_ratings", methods=["POST"])
def get_ratings():
	content = request.get_json()

	userId = str(content['userId'])
	type = content['type']

	rates = query("select id, reason, advice, productId from tester_rate where testerId = " + userId + " and type = '" + type + "' order by created desc", True).fetchall()

	for rate in rates:
		rate["key"] = "rate-" + str(rate["id"])

		product = query("select name, image from product where id = " + str(rate["productId"]), True).fetchone()

		rate["product"] = {
			"logo": json.loads(product["image"]),
			"name": product["name"]
		}

	return { "rates": rates }

@app.route("/update_first_time", methods=["POST"])
def update_first_time():
	content = request.get_json()

	userId = str(content['userId'])

	query("update user set firstTime = 0 where id = " + userId)

	return { "msg": "" }

@app.route("/get_payment_info", methods=["POST"])
def get_payment_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select tokens from user where id = " + userId, True).fetchone()

	if user != None:
		tokens = json.loads(user["tokens"])

		methods = stripe.PaymentMethod.list(
		  customer=tokens["customer"],
		  type="card",
		)
		card = None

		if len(methods.data) > 0:
			card = methods.data[0].card
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
		customer = stripe.Customer.list_sources(tokens["customer"], object="card", limit=1)

		if len(customer.data) == 0:
			stripe.Customer.create_source(
				tokens["customer"],
				source=token
			)
		else:
			stripe.Customer.modify(
				tokens["customer"],
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

	tester = query("select id, email, tokens from user where id = " + userId, True).fetchone()
	tokens = json.loads(tester["tokens"])

	earnings = query("select id, productId from product_testing where testerId = " + userId + " limit 5", True).fetchall()
	earnedAmount = 0.0
	pendingEarned = 0.0

	for info in earnings:
		product = query("select name, otherInfo, amountSpent from product where id = " + str(info["productId"]), True).fetchone()
		otherInfo = json.loads(product["otherInfo"])

		if otherInfo["charge"] != "" and otherInfo["transferGroup"] != "":
			transferGroup = otherInfo["transferGroup"]
			amount = product["amountSpent"] / 5

			transferAmount = int(amount * 100)
			balance = get_balance()
			earnedAmount += amount

			if balance >= transferAmount and pending == False:
				stripe.Transfer.create(
					amount=transferAmount,
					currency="cad",
					description="Rewarded $" + str(round(amount, 2)) + " to tester: " + tester["email"] + " of product: " + product["name"],
					destination=tokens["account"],
					transfer_group=transferGroup
				)
			else:
				query("insert into pending_payout (accountId, transferGroup, amount, email, created) values ('" + tokens["account"] + "', '" + transferGroup + "', " + str(transferAmount) + ", '" + tester["email"] + "', " + str(time()) + ")")

				pendingEarned += amount

			query("delete from product_testing where id = " + str(info["id"]))

	numLeftover = query("select count(*) as num from product_testing where testerId = " + userId, True).fetchone()["num"]

	return { 
		"earnedAmount": earnedAmount,
		"pendingEarned": pendingEarned > 0,
		"leftover": numLeftover > 0
	}

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
	content = request.get_json()

	userId = str(content['userId'])
	redirect = str(content['redirect'])

	user = query("select tokens from user where id = " + userId, True).fetchone()
	tokens = json.loads(user["tokens"])

	session = stripe.checkout.Session.create(
	  payment_method_types=['card'],
	  mode='setup',
	  customer=tokens["customer"],
	  success_url=os.getenv("CLIENT_URL") + '/' + redirect + '?session_id={CHECKOUT_SESSION_ID}',
	  cancel_url=os.getenv("CLIENT_URL") + '/' + redirect,
	)

	return { "url": session.url }

@app.route("/create_customer_payment", methods=["POST"])
def create_customer_payment():
	content = request.get_json()

	userId = str(content['userId'])
	productId = str(content['productId']) if "productId" in content and content["productId"] != None else None
	sessionId = content['sessionId'] if "sessionId" in content else None

	user = query("select tokens from user where id = " + userId, True).fetchone()
	tokens = json.loads(user["tokens"])
	customerId = tokens["customer"]

	paymentMethod = stripe.Customer.list_payment_methods(
		tokens["customer"],
		type="card",
	)
	methodId = paymentMethod.data[0].id

	if productId != None:
		product = query("select otherInfo from product where id = " + productId, True).fetchone()
		otherInfo = json.loads(product["otherInfo"])
		amount = launchAmount + appFee
		transferGroup = getId()
		charge = stripe.PaymentIntent.create(
			amount=int(amount * 100),
			currency="cad",
			customer=customerId,
			payment_method=methodId,
			transfer_group=transferGroup,
			confirm=True,
			automatic_payment_methods={
				"enabled": True,
				"allow_redirects": "never"
			}
		)
		chargeInfo = {
			"country": paymentMethod.data[0].card.country,
			"currency": charge.currency
		}
		amount = get_stripe_fee(chargeInfo, amount)
		payoutAmount = int((amount - launchAmount) * 100)
		balance = get_balance()

		if balance >= payoutAmount and pending == False:
			stripe.Payout.create(
				amount=payoutAmount,
				currency="cad"
			)
		else:
			query("insert into pending_payout (accountId, transferGroup, amount, email, created) values ('', '', " + str(payoutAmount) + ", '', " + str(time()) + ")")

		otherInfo = json.dumps({"charge": charge.id, "transferGroup": transferGroup})
		query("update product set otherInfo = '" + otherInfo + "', deposited = " + str(time()) + " where id = " + productId)
	else:
		charge = stripe.PaymentIntent.create(
			amount=int(regainAmount * 100),
			currency="cad",
			customer=customerId,
			payment_method=methodId,
			confirm=True,
			automatic_payment_methods={
				"enabled": True,
				"allow_redirects": "never"
			}
		)
		query("update user set isBanned = 0 where id = " + userId)

	if sessionId != None:
		info = stripe.checkout.Session.retrieve(sessionId)
		info = stripe.SetupIntent.retrieve(info.setup_intent)

		info = stripe.PaymentMethod.attach(
			info.payment_method,
			customer=customerId,
		)

	return { "msg": "" }

@app.route("/rate_customer", methods=["POST"])
def rate_customer():
	content = request.get_json()

	productId = str(content['productId'])
	testerId = str(content['testerId'])
	type = content['type']
	reason = content['reason']

	productTesting = query("select id, advice from product_testing where productId = " + productId + " and testerId = " + testerId, True).fetchone()
	query("insert into tester_rate (productId, testerId, testingId, type, reason, advice, created) values (" + productId + ", " + testerId + ",  " + str(productTesting["id"]) + ", '" + type + "', '" + reason + "', '" + pymysql.converters.escape_string(productTesting["advice"]) + "', " + str(time()) + ")")

	if type == "warn":
		tester = query("select email from user where id = " + testerId, True).fetchone()
		product = query("select name from product where id = " + productId, True).fetchone()
		warned = query("select count(*) as num from tester_rate where testerId = " + testerId, True).fetchone()["num"]

		if warned == 0:
			# email sent properly
			html = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	"
			html += "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: rgba(0, 0, 0, 0.5); }</style></head><body>	"
			html += "<div style='background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
			html += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div><h3 style='color: grey; text-align: center;'>BetaRush</h3>		</div>		"
			html += "<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			"
			html += "You have been warned to be banned because of an advice you gave for the product: " + product["name"] + ". Next time, you will be banned and will have to pay $10.00 to regain your account"
			html += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
			html += "<a class='button' style='border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;' href='" + os.getenv("CLIENT_URL")
			html += "/ratings'>See your ratings"
			html += "</a>		</div>	</div></body></html>"

			send_email(tester["email"], "You have been warned to be banned", html)
		else:
			query("update user set isBanned = 1 where id = " + testerId)

			html = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	"
			html += "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: rgba(0, 0, 0, 0.5); }</style></head><body>	"
			html += "<div style='background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
			html += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div><h3 style='color: grey; text-align: center;'>BetaRush</h3>		</div>		"
			html += "<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			"
			html += "You have been banned because of an advice you gave for the product: " + product["name"] + ". Pay $2.00 to regain your account"
			html += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
			html += "<a class='button' style='border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;' href='" + os.getenv("CLIENT_URL")
			html += "/ratings'>See your ratings"
			html += "</a>		</div>	</div></body></html>"

			send_email(tester["email"], "You have been banned", html)

	return { "msg": "" }
