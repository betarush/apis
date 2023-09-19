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
				k += 1

				pending = query("select * from pending_payout order by created", True).fetchone()

				if pending != None:
					amount = int(pending["amount"])
					
					if balance >= amount:
						if pending["accountId"] != '':
							stripe.Transfer.create(
								amount=amount,
								currency="cad",
								description="Rewarded $" + str(amount / 100) + " to tester",
								destination=pending["accountId"],
								transfer_group=pending["transferGroup"]
							)

							html = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	"
							html += "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: #000000; color: white; }</style></head><body>	"
							html += "<div style='background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; height: 500px; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
							html += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div>		</div>		"
							html += "<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			"

							html += "Yes! You have received your earnings in your bank account.<br/><br/>Thank you for your contribution"
							html += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
							html += "<a class='button' style='border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;' href='https://www.getproductfeedback.com"
							html += "'>Try more products and earn more</a>		</div>	</div></body></html>"
							
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
				else:
					break

				if k % 10 == 0:
					k = 0
					sleep(3)

		print("balance is zero", time())

		sleep(3)

	print("DONE")

# get process id: ps -ef | grep python
# start autopayout: nohup python payout.py &
