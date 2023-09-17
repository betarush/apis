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
	productId = str(content['productId'])
	feedback = content['feedback']

	product = query("select name, otherInfo, creatorId from product where id = " + productId, True).fetchone()
	testing = query("select id, feedback from product_testing where testerId = " + userId + " and productId = " + productId + " and feedback = ''", True).fetchone()
	creator = query("select email from user where id = " + str(product["creatorId"]), True).fetchone()

	if testing != None:
		html = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: #000000; color: white; }</style></head><body>	<div style='background-color: #efefef; border-radius: 20px; display: flex; flex-direction: column; height: 500px; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div>		</div>		<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			Yes! Someone just tried your product, " + product["name"] + " and gave you a feedback</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			<a class='button' style='border-radius: 10px; border-style: solid; border-width: 5px; color: black; font-size: 15px; margin: 10px auto; padding: 5px; text-align: center; text-decoration: none; width: 100px;' href='https://www.getproductfeedback.com/feedback/" + productId + ">Check it out</a>		</div>	</div></body></html>"

		send_email(creator["email"], "A customer gave you a feedback on your product", html)

		query("update product_testing set feedback = '" + pymysql.converters.escape_string(feedback) + "' where id = " + str(testing["id"]))

		return { "msg": "" }

	return { "status": "nonExist" }, 400

@app.route("/get_rejections", methods=["POST"])
def get_rejections():
	content = request.get_json()

	userId = str(content['userId'])

	rejections = query("select id, productId, feedback, rejectedReason from product_testing where testerId = " + userId + " and not rejectedReason = ''", True).fetchall()

	for rejection in rejections:
		product = query("select name, image from product where id = " + str(rejection["productId"]), True).fetchone()

		rejection["key"] = "rejection-" + str(rejection["id"])
		rejection["name"] = product["name"]
		rejection["logo"] = json.loads(product["image"])
		rejection["reason"] = rejection["rejectedReason"]

		del rejection["rejectedReason"]

	return { "rejections": rejections }
