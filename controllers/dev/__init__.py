from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message
from binascii import a2b_base64
from time import time, sleep
import os, json, pytz, datetime

cors = CORS(app)

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

@app.route("/simulate")
def simulate():
	runTime = 0
	creator = None
	account = None

	while runTime < 100:
		if creator == None: # list product
			creator = stripe.Customer.list(limit=1)

			if len(creator.data) > 0:
				creator = creator.data[0]
			else:
				creator = stripe.Customer.create(
					description="First startup product creator",
					email="dsldk@gmail.com"
				)
				stripe.Customer.create_source(
					creator.id,
					source="tok_bypassPending"
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
		transferGroup = "a transfer group: " + str(time())
		charge = stripe.Charge.create(
			amount=int(amount * 100),
			currency="cad",
			customer=creator.id,
			transfer_group=transferGroup
		)
		amount = get_stripe_fee(charge, amount)
		payoutAmount = round(amount - launchAmount, 2)
		stripe.Payout.create(
			currency="cad",
			amount=int(payoutAmount * 100)
		)
		print("creator paid: $" + str(round(launchAmount + appFee, 2)))
		print("payout to owner account: $" + str(round(payoutAmount, 2)))

		# payout
		num = [1, 2, 3, 4, 5]
		amount = launchAmount / 5

		for n in num:
			result = stripe.Transfer.create(
				amount=int(amount*100),
				currency="cad",
				description="Payout $" + str(round(amount, 2)) + " to tester: " + str(n),
				destination=account.id,
				source_transaction=charge.id,
				transfer_group=transferGroup
			)
			print("$" + str(round(amount, 2)) + " transferred to tester: " + str(n))

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

	query("alter table user auto_increment = 1")
	query("alter table product auto_increment = 1")
	query("alter table product_testing auto_increment = 1")

	return { "msg": "" }