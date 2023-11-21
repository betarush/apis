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

@app.route("/welcome_testing")
def welcome_testing():
	return "startupfeedback: Welcome to testing"

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
	content = request.get_json()

	userId = str(content['userId'])
	testingId = str(content['testingId'])
	advice = content['advice']

	user = query("select isBanned from user where id = " + userId, True).fetchone()
	testing = query("select id, advice, productId from product_testing where testerId = " + userId + " and id = " + testingId + " and advice = ''", True).fetchone()

	if testing != None and user["isBanned"] == 0: # email sent properly
		product = query("select name, otherInfo, creatorId, amountLeftover, amountSpent from product where id = " + str(testing["productId"]), True).fetchone()
		tester = query("select email from user where id = " + userId, True).fetchone()
		creator = query("select email from user where id = " + str(product["creatorId"]), True).fetchone()

		otherInfo = json.loads(product["otherInfo"])
		amount = float(product["amountLeftover"]) - (product["amountSpent"] / 5)
		rewardAmount = product["amountSpent"] / 5
	
		alertCreatorHtml = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	"
		alertCreatorHtml += "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: rgba(0, 0, 0, 0.5); }</style></head><body>	"
		alertCreatorHtml += "<div style='background-color: #efefef; border-radius: 10px; display: flex; flex-direction: column; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
		alertCreatorHtml += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div><h3 style='color: grey; text-align: center;'>BetaRush</h3>		</div>		"
		alertCreatorHtml += "<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			"

		alertCreatorHtml += "Yay! Someone tried your product, " + product["name"] + " and gave you an advice"
		alertCreatorHtml += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
		alertCreatorHtml += "<a class='button' style='border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;' href='" + os.getenv("CLIENT_URL")
		alertCreatorHtml += "/feedback/" + str(testing["productId"]) + "'>Check it out"
		alertCreatorHtml += "</a>		</div>	</div></body></html>"

		alertTesterHtml = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	"
		alertTesterHtml += "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: rgba(0, 0, 0, 0.5); }</style></head><body>	"
		alertTesterHtml += "<div style='background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
		alertTesterHtml += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div><h3 style='color: grey; text-align: center;'>BetaRush</h3>		</div>		"
		alertTesterHtml += "<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			"
		alertTesterHtml += "Congrats!! You have been rewarded $" + str(format(rewardAmount, ".2f")) + " for your advice/feedback on a product, " + product["name"]
		alertTesterHtml += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
		alertTesterHtml += "<a class='button' style='border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;' href='" + os.getenv("CLIENT_URL")
		alertTesterHtml += "/earnings'>Get your reward"
		alertTesterHtml += "</a>		</div>	</div></body></html>"

		send_email(creator["email"], "A customer gave you an advice on your product", alertCreatorHtml)
		send_email(tester["email"], "Wow, You have been rewarded $" + str(format(rewardAmount, ".2f")), alertTesterHtml)

		query("update product_testing set advice = '" + pymysql.converters.escape_string(advice) + "' where id = " + str(testing["id"]))
		query("update product set amountLeftover = " + str(round(amount, 2)) + " where id = " + str(testing["productId"]))

		return { "msg": "" }
	elif user["isBanned"] == 1:
		return { "banned": True }

	return { "status": "nonExist" }, 400
