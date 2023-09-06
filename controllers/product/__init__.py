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

	user = query("select tokens from user where id = " + userId, True).fetchone()

	if user != None:
		image = json.dumps({ "name": imageName, "width": round(image["width"], 2), "height": round(image["height"], 2) })
		tokens = json.loads(user["tokens"])

		amount = 10.00
		transferGroup = getId()
		charge = stripe.Charge.create(
			amount=int(amount * 100),
			currency="cad",
			customer=tokens["creator"],
			transfer_group=transferGroup
		)
		otherInfo = json.dumps({"charge": charge.id, "transferGroup": transferGroup})

		query("insert into product (name, image, info, link, creatorId, otherInfo, amount) values ('" + name + "', '" + image + "', '" + desc + "', '" + link + "', " + userId + ", '" + otherInfo + "', " + str(round(amount, 2)) + ")")

		return { "msg": "" }

	return { "status": "nonExist" }, 400

@app.route("/get_untested_products", methods=["POST"])
def get_untested_products():
	content = request.get_json()

	userId = str(content['userId'])

	sql = "select * from product where not creatorId = " + userId
	sql += " and ("
	sql += "(select count(*) from product_testing where testerId = " + userId + " and productId = product.id and testerId = " + userId + " and feedback = '') > 0"
	sql += " or "
	sql += "(select count(*) from product_testing where testerId = " + userId + " and productId = product.id) = 0"
	sql += ") and amount > 0"

	datas = query(sql, True).fetchall()

	for data in datas:
		amount = float(data["amount"])

		data["key"] = "product-" + str(data["id"])
		data["logo"] = json.loads(data["image"])

		testing = query("select id, feedback from product_testing where testerId = " + userId + " and productId = " + str(data["id"]), True).fetchone()

		data["trying"] = testing != None

		data["numTried"] = amount / 2

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

		testing = query("select earned from product_testing where productId = " + str(data["id"]), True).fetchone()

		data["earned"] = testing["earned"] == True

	return { "products": datas }

@app.route("/get_my_products", methods=["POST"])
def get_my_products():
	content = request.get_json()

	userId = str(content['userId'])

	sql = "select * from product where creatorId = " + userId

	datas = query(sql, True).fetchall()

	for data in datas:
		data["key"] = "product-" + str(data["id"])
		data["logo"] = json.loads(data["image"])

		otherInfo = json.loads(data["otherInfo"])
		charge = stripe.Charge.retrieve(otherInfo["charge"])
		data["amountSpent"] = round(charge.amount / 100, 2)

		testing = query("select count(*) from product_testing where productId = " + str(data["id"]) + " and earned = 0", True).fetchone()["count(*)"]
		tested = query("select count(*) from product_testing where productId = " + str(data["id"]) + " and not feedback = '' and earned = 0", True).fetchone()["count(*)"]

		data["numTesting"] = testing
		data["numFeedback"] = tested
		data["numTested"] = 5 - (int(data["amount"]) / 2)

	return { "products": datas }

@app.route("/try_product", methods=["POST"])
def try_product():
	content = request.get_json()

	userId = str(content['userId'])
	productId = str(content['productId'])

	testing = True

	testing = query("select * from product_testing where testerId = " + userId + " and productId = " + productId, True).fetchone()

	if testing == None: # haven't tried yet
		query("insert into product_testing (testerId, productId, feedback, earned) values (" + userId + ", " + productId + ", '', 0)")

	return { "msg": "" }

@app.route("/get_feedbacks", methods=["POST"])
def get_feedbacks():
	content = request.get_json()

	productId = str(content['productId'])

	feedbacks = query("select id, feedback, testerId from product_testing where productId = " + productId + " and earned = 0", True).fetchall()
	product = query("select name, image from product where id = " + productId, True).fetchone()

	for info in feedbacks:
		info["key"] = "feedback-" + str(info["id"])
		info["header"] = info["feedback"]

		del info["feedback"]

	return { "feedbacks": feedbacks, "name": product["name"], "logo": json.loads(product["image"] )}


