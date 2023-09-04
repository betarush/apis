from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message
from binascii import a2b_base64
import os, json

cors = CORS(app)

@app.route("/welcome_product")
def welcome_product():
	return "startupfeedback: Welcome to product"

@app.route("/list_product", methods=["POST"])
def list_product():
	content = request.get_json()

	name = content['name']
	desc = content['desc']
	link = content['link']
	image = json.loads(content['image'])

	imageName = getId() + ".jpg"

	data = a2b_base64(image["uri"].split(",")[1])
	fd = open(os.path.join("static", imageName), 'wb')
	fd.write(data)
	fd.close()

	image = json.dumps({ "name": imageName, "width": round(image["width"], 2), "height": round(image["height"], 2) })

	query("insert into product (name, image, info, link) values ('" + name + "', '" + image + "', '" + desc + "', '" + link + "')")

	return { "msg": "" }
