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
