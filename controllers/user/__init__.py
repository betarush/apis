from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message

cors = CORS(app)

@app.route("/welcome_user")
def welcome_user():
	return "startupfeedback: Welcome to user"

@app.route("/register", methods=["POST"])
def register():
	content = request.get_json()

	email = content['email']
	password = content['password']
	username = "user" + getId()

	userId = query("insert into user (email, password, username, earnings) values ('" + email + "', '" + generate_password_hash(password) + "', '" + username + "', 0.0)", True).lastrowid

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

@app.route("/get_user_info", methods=["POST"])
def get_user_info():
	content = request.get_json()

	userId = str(content['userId'])

	user = query("select email from user where id = " + userId, True).fetchone()

	if user != None:
		username = user["email"].split("@")[0]

		return { "username": username }

	return { "status": "nonExist" }, 400

