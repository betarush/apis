from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message
from binascii import a2b_base64
from time import time
import os, json

cors = CORS(app)

@app.route("/welcome_dev")
def welcome_dev():
	return "startupfeedback: Welcome to product"

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