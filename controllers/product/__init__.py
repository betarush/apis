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

	userId = str(content['userId'])
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

	query("insert into product (name, image, info, link, creatorId) values ('" + name + "', '" + image + "', '" + desc + "', '" + link + "', " + userId + ")")

	return { "msg": "" }

@app.route("/get_untested_products", methods=["POST"])
def get_untested_products():
	content = request.get_json()

	userId = str(content['userId'])

	sql = "select * from product where not creatorId = " + userId
	sql += " and ("
	sql += "(select count(*) from product_testing where testerId = " + userId + " and productId = product.id and testerId = " + userId + " and feedback = '') > 0"
	sql += ")"

	datas = query(sql, True).fetchall()

	for data in datas:
		data["key"] = "product-" + str(data["id"])
		data["logo"] = json.loads(data["image"])

		testing = query("select id, feedback from product_testing where testerId = " + userId + " and productId = " + str(data["id"]), True).fetchone()

		data["trying"] = testing != None

	return { "products": datas }

@app.route("/get_tested_products", methods=["POST"])
def get_tested_products():
	content = request.get_json()

	userId = str(content['userId'])

	sql = "select * from product where not creatorId = " + userId
	sql += " and (select count(*) from product_testing where productId = product.id and testerId = " + userId + " and not feedback = '') > 0"

	datas = query(sql, True).fetchall()

	for data in datas:
		data["key"] = "product-" + str(data["id"])
		data["logo"] = json.loads(data["image"])

	return { "products": datas }

@app.route("/try_product", methods=["POST"])
def try_product():
	content = request.get_json()

	userId = str(content['userId'])
	productId = str(content['productId'])

	testing = True

	testing = query("select * from product_testing where testerId = " + userId + " and productId = " + productId, True).fetchone()

	if testing == None: # haven't tried yet
		query("insert into product_testing (testerId, productId, feedback) values (" + userId + ", " + productId + ", '')")

	return { "msg": "" }

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

