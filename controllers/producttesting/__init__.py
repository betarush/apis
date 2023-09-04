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

		user = query("select id, email, tokens from user where id = " + userId, True).fetchone()

		if user != None:
			# tokens = json.loads(user["tokens"])

			# if tokens["account"] == "":
			# 	account = stripe.Account.create(
			# 		type="custom",
			# 		country="CA",
			# 		email=user["email"],
			# 		capabilities={
			# 	    "card_payments": {"requested": True},
			# 	    "transfers": {"requested": True},
			# 	  },
			# 	  business_type="individual",
			# 	  individual={
			# 	  	"address": { 
			# 	  		"line1": "1111 Dundas St",
			# 	  		"postal_code": "M4M3H5" 
			# 	  	},
			# 	  	"dob": {
			# 	  		"day": 31,
			# 	  		"month": 12,
			# 	  		"year": 1990
			# 	  	},
			# 	  	"first_name": "Jenny",
			# 	  	"last_name": "Rosen"
			# 	  },
			# 	  external_account="btok_us_verified",
			# 	  tos_acceptance={"date": int(time()), "ip": "8.8.8.8"}
			# 	)

			# 	tokens["account"] = account.id

			# 	query("update user set tokens = '" + json.dumps(tokens) + "' where id = " + userId)

			return { "msg": "" }

	return { "status": "nonExist" }, 400
