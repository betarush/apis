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

	testing = query("select id, feedback from product_testing where testerId = " + userId + " and productId = " + productId + " and feedback = ''", True).fetchone()

	if testing != None:
		query("update product_testing set feedback = '" + pymysql.converters.escape_string(feedback) + "' where id = " + str(testing["id"]))

		return { "msg": "" }

	return { "status": "nonExist" }, 400
