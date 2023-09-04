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

