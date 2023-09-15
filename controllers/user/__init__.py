from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message

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

@app.route("/verify", methods=["POST"])
def verify():
	content = request.get_json()

	email = content['email']

	verifyCode = ""

	for n in range(4):
		verifyCode += str(randint(0, 9))

	msg = Message(
		"Feedback Verification Code",
		sender=('Product Feedback', 'admin@geottuse.com'),
		recipients = [email],
		html="""
			<html>
				<head>
					<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap" rel="stylesheet"/>
					<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap" rel="stylesheet"/>
					<style>.button:hover { background-color: #000000; color: white; }</style>
				</head>
				<body>
					<div style="background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; height: 200px; justify-content: space-around; width: 500px;">
						<div style='width: 100%;'>
							<div style="height: 10vw; margin: 10px auto 0 auto; width: 10vw;">
								<img style="height: 100%; width: 100%;" src="http://www.getproductfeedback.com/favicon.ico"/>
							</div>
						</div>
						<div style="color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;">
							Your verification code is """ + verifyCode + """
						</div>
					</div>
				</body>
			</html>
		"""
	)

	try:
		mail.send(msg)
	except:
		print("")

	return { "verifycode": verifyCode }

@app.route("/get_user_info", methods=["POST"])
def get_user_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select email, tokens from user where id = " + userId, True).fetchone()

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
	pendingEarned = 0.0

	for info in earnings:
		product = query("select name, otherInfo from product where id = " + str(info["productId"]), True).fetchone()
		otherInfo = json.loads(product["otherInfo"])
		transferGroup = otherInfo["transferGroup"]
		amount = launchAmount / 5

		transferAmount = int(amount * 100)
		balance = get_balance()

		if balance >= transferAmount:
			stripe.Transfer.create(
				amount=transferAmount,
				currency="cad",
				description="Rewarded $" + str(round(amount, 2)) + " to tester: " + tester["email"] + " of product: " + product["name"],
				destination=tokens["account"],
				transfer_group=transferGroup
			)

			earnedAmount += amount
		else:
			query("insert into pending_payout (accountId, transferGroup, amount, created) values ('" + tokens["account"] + "', '" + transferGroup + "', " + str(transferAmount) + ", " + str(time()) + ")")

			pendingEarned += amount

		query("delete from product_testing where id = " + str(info["id"]))

	return { 
		"earnedAmount": earnedAmount,
		"pendingEarned": pendingEarned
	}

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select tokens from user where id = " + userId, True).fetchone()
	tokens = json.loads(user["tokens"])

	session = stripe.checkout.Session.create(
	  payment_method_types=['card'],
	  mode='setup',
	  customer=tokens["creator"],
	  success_url=os.getenv("CLIENT_URL") + '/listproduct?session_id={CHECKOUT_SESSION_ID}',
	  cancel_url=os.getenv("CLIENT_URL") + '/listproduct',
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

	product = query("select name, amount from product where id = " + productId, True).fetchone()
	amount = float(product["amount"]) - (launchAmount / 5)
	tester = query("select email from user where id = " + testerId, True).fetchone()

	try:
		msg = Message(
			"Wow, You have been rewarded $4.00",
			sender=('Product Feedback', 'admin@geottuse.com'),
			recipients = [tester["email"]],
			html="""
				<html>
					<head>
						<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap" rel="stylesheet"/>
						<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap" rel="stylesheet"/>
						<style>.button:hover { background-color: #000000; color: white; }</style>
					</head>
					<body>
						<div style="background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; height: 500px; justify-content: space-around; width: 500px;">
							<div style='width: 100%;'>
								<div style="height: 10vw; margin: 10px auto 0 auto; width: 10vw;">
									<img style="height: 100%; width: 100%;" src="http://www.getproductfeedback.com/favicon.ico"/>
								</div>
							</div>
							<div style="color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;">
								Congrats!! You have been rewarded $4.00 for your feedback on a product, """ + product["name"] + """
								Click below to withdraw your reward
							</div>
							<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>
								<a class="button" style="border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;" href="https://www.getproductfeedback.com/earnings">Get your reward</a>
							</div>
						</div>
					</body>
				</html>
			"""
		)

		mail.send(msg)

		query("update product set amount = " + str(round(amount, 2)) + " where id = " + productId)
		query("update product_testing set earned = 1 where productId = " + productId + " and testerId = " + testerId)

		return { "msg": "" }
	except:
		print("")

	return { "status": "failed to send" }, 400

@app.route("/reject_feedback", methods=["POST"])
def reject_feedback():
	content = request.get_json()

	productId = str(content['productId'])
	testerId = str(content['testerId'])
	reason = content['reason']

	tester = query("select email from user where id = " + testerId, True).fetchone()

	try:
		msg = Message(
			"Sorry, one of your feedback has been rejected",
			sender=('Product Feedback', 'admin@geottuse.com'),
			recipients = [tester["email"]],
			html="""
				<html>
					<head>
						<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap" rel="stylesheet"/>
						<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap" rel="stylesheet"/>
						<style>.button:hover { background-color: #000000; color: white; }</style>
					</head>
					<body>
						<div style="background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; height: 200px; justify-content: space-around; width: 500px;">
							<div style='width: 100%;'>
								<div style="height: 10vw; margin: 10px auto 0 auto; width: 10vw;">
									<img style="height: 100%; width: 100%;" src="http://www.getproductfeedback.com/favicon.ico"/>
								</div>
							</div>
							<div style="color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;">
								Your feedback was rejected
								""" 
								+ (" with a reason: " + str(reason) if str(reason) != "" else "") + 
								"""
							</div>
							<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>
								<a class="button" style="border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;" href="https://www.getproductfeedback.com/rejections">See the rejection</a>
							</div>
						</div>
					</body>
				</html>
			"""
		)

		mail.send(msg)

		query("update product_testing set rejectedReason = '" + reason + "' where productId = " + productId + " and testerId = " + testerId)
	except:
		print("")

	return { "msg": "" }

