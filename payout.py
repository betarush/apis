import pymysql.cursors, json, os
from functions import *
from flask import Flask
from flask_mail import Mail, Message
from time import time, sleep

app = Flask(__name__)
app.config['MAIL_SERVER']='smtp.zoho.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'admin@geottuse.com'
app.config['MAIL_PASSWORD'] = 'q0rtghsdui!Fwug'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

with app.app_context():
	while True:
		balance = get_balance()
		k = 0

		numPayoutPending = query("select count(*) as num from pending_payout where amount < " + str(balance + 1), True).fetchone()["num"]
		numPending = query("select count(*) as num from pending_payout", True).fetchone()["num"]

		print("num pending: " + str(numPayoutPending) + ":" + str(numPending) + ":" + str(balance))

		if balance > 0 and numPayoutPending > 0:
			while True: # part is looping on one record
				pending = query("select * from pending_payout order by created", True).fetchone()
				amount = int(pending["amount"])
				k += 1

				if balance >= amount:
					if pending["accountId"] != '':
						stripe.Transfer.create(
							amount=amount,
							currency="cad",
							description="Rewarded $" + str(amount / 100) + " to tester",
							destination=pending["accountId"],
							transfer_group=pending["transferGroup"]
						)

						print("Rewarded $" + str(amount / 100) + " to tester")
					else:
						stripe.Payout.create(
							amount=amount,
							currency="cad"
						)

						print("Rewarded $" + str(round(amount / 100, 2)) + " to owner")

					query("delete from pending_payout where id = " + str(pending["id"]))

					balance -= amount

					print("balance reduced to " + str(balance) + " with amount at " + str(amount) + " with account id: " + pending["accountId"])

					if k % 10 == 0:
						sleep(3)

				if balance == 0:
					sleep(3)

					break

		print("balance is zero", time())

		sleep(3)
