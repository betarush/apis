from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message
from binascii import a2b_base64
from time import time, sleep
import os, json, pytz, datetime, requests

app.config['MAIL_SERVER']='smtp.zoho.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'admin@geottuse.com'
app.config['MAIL_PASSWORD'] = 'q0rtghsdui!Fwug'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

cors = CORS(app)
mail = Mail(app)

@app.route("/welcome_dev")
def welcome_dev():
	return "startupfeedback: Welcome to product"

@app.route("/read_charge")
def read_charge():
	info = stripe.Charge.retrieve("ch_3No92rFqjgkiO0WH0F7pID2V")

	country = info.payment_method_details.card.country
	currency = info.currency

	tz = pytz.timezone('America/Toronto')
	timenow = str(datetime.datetime.now(tz))
	updatetime = "2023-10-15 00:00:00.00-00:00"

	return { "country": country, "currency": currency, "timenow": timenow, "updatenow": timenow >= updatetime }

@app.route("/create_card")
def create_card():
	card = stripe.Token.create(
	  card={
	    "number": "4000002500001001",
	    "exp_month": 9,
	    "exp_year": 2024,
	    "cvc": "314",
	  },
	)

	return card

@app.route("/simulate")
def simulate():
	runTime = 0
	creator = None
	account = None

	# pm_card_bypassPending
	# pm_card_us

	while runTime < 10:
		if creator == None: # list product
			creator = stripe.Customer.list(limit=1)

			if len(creator.data) > 0:
				creator = creator.data[0]
			else:
				creator = stripe.Customer.create(
					description="First startup product creator",
					email="dsldk@gmail.com"
				)

			paymentMethod = stripe.Customer.list_payment_methods(
			  creator.id,
			  type="card",
			)

			if len(paymentMethod.data) == 0:
				stripe.PaymentMethod.attach(
					"pm_card_bypassPending",
					customer=creator.id
				)

		if account == None: # receive payment
			account = stripe.Account.list(limit=1)

			if len(account.data) > 0:
				account = account.data[0]
			else:
				account = stripe.Account.create(
					type="custom",
					country="CA",
					email="jenny.rosen@example.com",
					capabilities={
				    "card_payments": {"requested": True},
				    "transfers": {"requested": True},
				  },
				  business_type="individual",
				  individual={
				  	"address": { 
				  		"line1": "1111 Dundas St",
				  		"postal_code": "M4M3H5" 
				  	},
				  	"dob": {
				  		"day": 31,
				  		"month": 12,
				  		"year": 1990
				  	},
				  	"first_name": "dsldk",
				  	"last_name": " dsldk dsldk"
				  },
				  external_account="btok_us_verified",
				  tos_acceptance={"date": int(time()), "ip": "8.8.8.8"},
				  settings={"payouts":{"schedule":{"interval":"manual"}}}
				)

		amount = launchAmount + appFee
		transferGroup = getId()
		paymentMethod = stripe.Customer.list_payment_methods(
		  creator.id,
		  type="card",
		)
		methodId = paymentMethod.data[0].id
		charge = stripe.PaymentIntent.create(
			amount=int(amount * 100),
			currency="cad",
			customer=creator.id,
			payment_method=methodId,
			transfer_group=transferGroup,
			confirm=True,
			automatic_payment_methods={
				"enabled": True,
				"allow_redirects": "never"
			}
		)
		print("creator paid: $" + str(round(amount, 2)))
		chargeInfo = {
			"country": paymentMethod.data[0].card.country,
			"currency": charge.currency
		}
		amount = get_stripe_fee(chargeInfo, amount)
		payoutAmount = round(amount - launchAmount, 2)

		balance = get_balance()

		if balance >= int(payoutAmount * 100):
			stripe.Payout.create(
				currency="cad",
				amount=int(payoutAmount * 100)
			)
			print("payout to owner account: $" + str(round(payoutAmount, 2)))
		else:
			query("insert into pending_payout (accountId, transferGroup, amount, created) values ('', '', " + str(int(payoutAmount * 100)) + ", " + str(time()) + ")")
			print("inserted into pending payout")

		# payout
		num = [1, 2, 3, 4, 5]
		amount = launchAmount / 5

		for n in num:
			balance = get_balance()

			if balance >= int(amount * 100):
				result = stripe.Transfer.create(
					amount=int(amount * 100),
					currency="cad",
					description="Payout $" + str(round(amount, 2)) + " to tester: " + str(n),
					destination=account.id,
					transfer_group=transferGroup
				)
				print("$" + str(round(amount, 2)) + " transferred to tester: " + str(n))
			else:
				query("insert into pending_payout (accountId, transferGroup, amount, created) values ('" + account.id + "', '" + transferGroup + "', " + str(int(amount * 100)) + ", " + str(time()) + ")")
				print("inserted into pending payout for tester")

		balance = stripe.Balance.retrieve()
		runTime += 1

		print("balance: $" + str(balance.available[0].amount / 100) + " at run: " + str(runTime))
		print(" ")
		print(" ")

	return { "num": runTime }

@app.route("/reset")
def reset():
	files = os.listdir("static")

	for file in files:
		if "jpg" in file:
			os.unlink("static/" + file)

	query("delete from user")
	query("delete from product")
	query("delete from product_testing")
	query("delete from pending_payout")
	query("delete from tester_rate")

	query("alter table user auto_increment = 1")
	query("alter table product auto_increment = 1")
	query("alter table product_testing auto_increment = 1")
	query("alter table pending_payout auto_increment = 1")
	query("alter table tester_rate auto_increment = 1")

	return { "msg": "" }

@app.route("/charge")
def charge():
	info = stripe.PaymentIntent.create(
		amount=2000,
		currency="cad",
		customer="cus_OdbGiPhpIPaKPt",
		payment_method="pm_card_bypassPending",
		automatic_payment_methods={
			"enabled": True,
			"allow_redirects": "never"
		}
	)
	info = stripe.PaymentIntent.confirm(info.id)

	return { "info": info }

@app.route("/send_email")
def send_email():
	html = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: #000000; color: white; }</style></head><body>	<div style='background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; height: 500px; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div>		</div>		<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			Yes! Someone just tried your product,  and gave you a feedback		</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			<a class='button' style='border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;' href='https://www.getproductfeedback.com/feedback'>Check it out</a>		</div>	</div></body></html>"

	payload = """
		{
			\"from\": { \"address\": \"admin@geottuse.com\"},
			\"to\": [
				{\"email_address\": {\
					"address\": \"kmrobogram@gmail.com\",
					\"name\": \"kmrobogram@gmail.com\"
				}}
			],
			\"subject\":\"Product Feedback\",
			\"htmlbody\":\"""" + html + """\"\n
		}
	"""
	headers = {
		'accept': "application/json",
		'content-type': "application/json",
		'authorization': "Zoho-enczapikey wSsVR60jrx70XKwszmWqIOo5m15RA1+gRhh8igby6SX7Ta2U8Mc8khfHB1CnSvIZGWRuRmdAorp6zh4F2zEI2oslmVoDASiF9mqRe1U4J3x17qnvhDzKXm1fmhOPLY0BwQ9sm2dlFMgk+g==",
	}

	response = requests.request("POST", "https://api.zeptomail.com/v1.1/email", data=payload, headers=headers)

	return { "msg": response.text }