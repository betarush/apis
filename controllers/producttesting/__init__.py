from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message

cors = CORS(app)

@app.route("/welcome_testing")
def welcome_testing():
	return "startupfeedback: Welcome to testing"

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
	content = request.get_json()

	userId = str(content['userId'])
	productId = str(content['productId'])
	feedback = content['feedback']

	product = query("select otherInfo from product where id = " + productId, True).fetchone()
	testing = query("select id, feedback from product_testing where testerId = " + userId + " and productId = " + productId + " and feedback = ''", True).fetchone()

	if testing != None:
		query("update product_testing set feedback = '" + pymysql.converters.escape_string(feedback) + "' where id = " + str(testing["id"]))

		return { "msg": "" }

	return { "status": "nonExist" }, 400

@app.route("/get_rejections", methods=["POST"])
def get_rejections():
	content = request.get_json()

	userId = str(content['userId'])

	rejections = query("select id, productId, rejectedReason from product_testing where testerId = " + userId + " and not rejectedReason = ''", True).fetchall()

	for rejection in rejections:
		product = query("select name, image from product where id = " + str(rejection["productId"]), True).fetchone()

		rejection["key"] = "rejection-" + str(rejection["id"])
		rejection["name"] = product["name"]
		rejection["logo"] = json.loads(product["image"])
		rejection["header"] = rejection["rejectedReason"]

		del rejection["rejectedReason"]

	return { "rejections": rejections }
