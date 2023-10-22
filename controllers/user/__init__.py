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

	password = generate_password_hash(password)

	userId = query("insert into user (email, password, username, earnings, bankaccountInfo, tokens, firstTime) values ('" + email + "', '" + password + "', '" + username + "', 0.0, '" + bankaccountInfo + "', '" + tokens + "', 1)", True).lastrowid

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
		html += "<div style='background-color: #efefef; border-radius: 10px; display: flex; flex-direction: column; height: 200px; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
		html += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div><h3 style='color: grey; text-align: center;'>WAVER</h3>		</div>		"
		html += "<div style='color: black; font-size: 25px; font-weight: bold; margin: 0 10%; text-align: center;'>			"
		html += "Your verification code is " + verifyCode
		html += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
		html += "</div>	</div></body></html>"

		send_email(email, "Waver Verification Code", html)

		return { "verifycode": verifyCode }

	return { "status": "exist" }, 400

@app.route("/get_user_info", methods=["POST"])
def get_user_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select email, tokens, firstTime from user where id = " + userId, True).fetchone()

	if user != None:
		username = user["email"].split("@")[0]
		tokens = json.loads(user["tokens"])

		if tokens["creator"] != "":
			paymentMethod = stripe.Customer.list_payment_methods(
			  tokens["creator"],
			  type="card",
			)
			paymentMethod = len(paymentMethod.data) > 0
		else:
			paymentMethod = False

		if tokens["account"] != "":
			account = stripe.Account.retrieve(tokens["account"])
			account = len(account.external_accounts.data) > 0
		else:
			account = False

		rejectedReasons = query("select count(*) as num from product_testing where testerId = " + userId + " and not rejectedReason = ''", True).fetchone()["num"]
		numCreatedProducts = query("select count(*) as num from product where creatorId = " + userId, True).fetchone()["num"]
		amountEarned = query("select sum(amountSpent / 5) as earnings from product where id in (select productId from product_testing where earned = 1 and testerId = " + userId + ")", True).fetchone()
		earnings = 0

		if amountEarned["earnings"] != None:
			earnings = round(amountEarned["earnings"], 2)

		return {
			"username": username,
			"earnings": earnings,
			"rejectedReasons": rejectedReasons,
			"paymentDone": paymentMethod,
			"bankaccountDone": account,
			"firstTime": user["firstTime"],
			"isCreator": numCreatedProducts > 0
		}

	return { "status": "nonExist" }, 400

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
		  customer=tokens["creator"],
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

	tester = query("select id, email, tokens from user where id = " + userId, True).fetchone()
	tokens = json.loads(tester["tokens"])

	earnings = query("select id, productId from product_testing where testerId = " + userId + " and earned = 1 limit 5", True).fetchall()
	earnedAmount = 0.0
	pendingEarned = 0.0

	for info in earnings:
		product = query("select name, otherInfo, amountSpent from product where id = " + str(info["productId"]), True).fetchone()
		otherInfo = json.loads(product["otherInfo"])
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

	numLeftover = query("select count(*) as num from product_testing where testerId = " + userId + " and earned = 1", True).fetchone()["num"]

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
	  customer=tokens["creator"],
	  success_url=os.getenv("CLIENT_URL") + '/' + redirect + '?session_id={CHECKOUT_SESSION_ID}',
	  cancel_url=os.getenv("CLIENT_URL") + '/' + redirect,
	)

	return { "url": session.url }

@app.route("/create_customer_payment", methods=["POST"])
def create_customer_payment():
	content = request.get_json()

	userId = str(content['userId'])
	sessionId = content['sessionId']

	user = query("select tokens from user where id = " + userId, True).fetchone()
	tokens = json.loads(user["tokens"])
	creatorId = tokens["creator"]

	info = stripe.checkout.Session.retrieve(sessionId)
	info = stripe.SetupIntent.retrieve(info.setup_intent)

	info = stripe.PaymentMethod.attach(
	  info.payment_method,
	  customer=creatorId,
	)

	return { "msg": "" }

@app.route("/reward_customer", methods=["POST"])
def reward_customer():
	content = request.get_json()

	productId = str(content['productId'])
	testerId = str(content['testerId'])

	product = query("select name, amountLeftover, amountSpent from product where id = " + productId, True).fetchone()
	amount = float(product["amountLeftover"]) - (product["amountSpent"] / 5)
	tester = query("select email from user where id = " + testerId, True).fetchone()

	rewardAmount = product["amountSpent"] / 5

	# email sent properly
	html = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	"
	html += "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: rgba(0, 0, 0, 0.5); }</style></head><body>	"
	html += "<div style='background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; height: 400px; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
	html += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div><h3 style='color: grey; text-align: center;'>WAVER</h3>		</div>		"
	html += "<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			"
	html += "Congrats!! You have been rewarded $" + str(format(rewardAmount, ".2f")) + " for your advice/feedback on a product, " + product["name"]
	html += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
	html += "<a class='button' style='border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;' href='" + os.getenv("CLIENT_URL")
	html += "/earnings'>Get your reward"
	html += "</a>		</div>	</div></body></html>"

	send_email(tester["email"], "Wow, You have been rewarded $" + str(format(rewardAmount, ".2f")), html)

	query("update product set amountLeftover = " + str(round(amount, 2)) + " where id = " + productId)
	query("update product_testing set earned = 1 where productId = " + productId + " and testerId = " + testerId)

	return { "msg": "" }

@app.route("/reject_feedback", methods=["POST"])
def reject_feedback():
	content = request.get_json()

	productId = str(content['productId'])
	testerId = str(content['testerId'])
	reason = content['reason']

	tester = query("select email from user where id = " + testerId, True).fetchone()

	html = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	"
	html += "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: #000000; color: white; }</style></head><body>	"
	html += "<div style='background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; height: 500px; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
	html += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div>		</div>		"
	html += "<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			"
	html += "Your advice/feedback was rejected" + (" with a reason: " + str(reason) if str(reason) != "" else "")
	html += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
	html += "<a class='button' style='border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;' href='" + os.getenv("CLIENT_URL")
	html += "/rejections'>See the rejection"
	html += "</a>		</div>	</div></body></html>"

	send_email(tester["email"], "Sorry, one of your advice/feedback has been rejected", html)

	query("update product_testing set rejectedReason = '" + reason + "' where productId = " + productId + " and testerId = " + testerId)

	return { "msg": "" }

