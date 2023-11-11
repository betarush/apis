from flask import Flask, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from models import *
from functions import *
from flask_mail import Mail, Message
from binascii import a2b_base64
from time import time
import os, json, requests

app.config['MAIL_SERVER']='smtp.zoho.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'admin@geottuse.com'
app.config['MAIL_PASSWORD'] = 'q0rtghsdui!Fwug'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

cors = CORS(app)
mail = Mail(app)

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

	user = query("select tokens, firstTime from user where id = " + userId, True).fetchone()

	if user != None:
		image = json.dumps({ "name": imageName, "width": round(image["width"], 2), "height": round(image["height"], 2) })

		otherInfo = json.dumps({ "charge": "", "transferGroup": "" })
		query("insert into product (name, image, info, link, creatorId, otherInfo, amountLeftover, amountSpent) values ('" + name + "', '" + image + "', '" + desc + "', '" + link + "', " + userId + ", '" + otherInfo + "', " + str(round(launchAmount, 2)) + ", " + str(round(launchAmount, 2)) + ")")

		if user["firstTime"] == True:
			query("update user set firstTime = 0 where id = " + userId)

		return { "msg": "" }

	return { "status": "nonExist" }, 400

@app.route("/relist_product", methods=["POST"])
def relist_product():
	content = request.get_json()

	productId = str(content['productId'])

	product = query("select id from product where id = " + productId, True).fetchone()

	if product != None:
		otherInfo = json.dumps({ "charge": "", "transferGroup": "" })
		query("update product set amountLeftover = " + str(round(launchAmount, 2)) + ", otherInfo = '" + otherInfo + "' where id = " + productId)

		return { "msg": "" }

	return { "status": "nonExist" }, 400

@app.route("/get_untested_products", methods=["POST"])
def get_untested_products():
	content = request.get_json()

	userId = str(content['userId'])
	offset = content['offset']

	sql = "select * from product where not creatorId = " + userId
	sql += " and (select count(*) from product_testing where testerId = " + userId + " and productId = product.id) = 0 and amountLeftover > 0 limit " + str(offset) + ", 10"

	datas = query(sql, True).fetchall()

	for data in datas:
		amount = float(data["amountLeftover"])

		data["key"] = "product-" + str(data["id"])
		data["logo"] = json.loads(data["image"])

		testing = query("select id, advice from product_testing where testerId = " + userId + " and productId = " + str(data["id"]) + " and advice = ''", True).fetchone()

		data["trying"] = testing != None

		data["numLeftover"] = 5 - ((data["amountSpent"] - data["amountLeftover"]) / (data["amountSpent"] / 5))
		data["reward"] = data["amountSpent"] / 5

	return { "products": datas, "offset": len(datas) + offset }

@app.route("/get_testing_products", methods=["POST"])
def get_testing_products():
	content = request.get_json()

	userId = str(content['userId'])
	offset = content['offset']

	sql = "select * from product where not creatorId = " + userId
	sql += " and (select count(*) from product_testing where productId = product.id and testerId = " + userId + ") > 0 limit " + str(offset) + ", 10"

	datas = query(sql, True).fetchall()

	for data in datas:
		data["key"] = "product-" + str(data["id"])
		data["logo"] = json.loads(data["image"])

		testing = query("select advice from product_testing where productId = " + str(data["id"]), True).fetchone()

		data["gave_feedback"] = testing["advice"] != ""
		data["reward"] = data["amountSpent"] / 5

	return { "products": datas, "offset": len(datas) + offset }

@app.route("/get_my_products", methods=["POST"])
def get_my_products():
	content = request.get_json()

	userId = str(content['userId'])
	offset = content['offset']

	sql = "select *, "

	# testing
	sql += "(select count(*) from product_testing where productId = product.id and advice = '') as numTesting, "
	sql += "("
	sql += "select count(*) from product_testing where productId = product.id and not advice = '' and ("
	sql += "select count(*) from tester_rate where productId = product_testing.productId and testerId = product_testing.testerId and testingId = product_testing.id"
	sql += ") = 0"
	sql += ") as numFeedback "
	sql += "from product where creatorId = " + userId + " limit " + str(offset) + ", 10"

	datas = query(sql, True).fetchall()

	for data in datas:
		data["key"] = "product-" + str(data["id"])
		data["logo"] = json.loads(data["image"])

		otherInfo = json.loads(data["otherInfo"])

		data["deposited"] = otherInfo["charge"] != ""
		data["amountSpent"] = round(data["amountSpent"], 2)
		data["numLeftover"] = 5 - ((data["amountSpent"] - data["amountLeftover"]) / (data["amountSpent"] / 5))
		
	return { "products": datas, "offset": len(datas) + offset }

@app.route("/try_product", methods=["POST"])
def try_product():
	content = request.get_json()

	userId = str(content['userId'])
	productId = str(content['productId'])

	user = query("select isBanned from user where id = " + userId, True).fetchone()
	testing = query("select * from product_testing where testerId = " + userId + " and productId = " + productId, True).fetchone()

	if testing == None and user["isBanned"] == 0: # haven't tried yet
		product = query("select creatorId, name from product where id = " + productId, True).fetchone()
		creator = query("select email from user where id = " + str(product["creatorId"]), True).fetchone()

		# email sent properly
		html = "<html><head>	<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	"
		html += "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap' rel='stylesheet'/>	<style>.button:hover { background-color: rgba(0, 0, 0, 0.5); }</style></head><body>	"
		html += "<div style='background-color: #efefef; border-radius: 10px; display: flex; flex-direction: column; justify-content: space-around; width: 500px;'>		<div style='width: 100%;'>			"
		html += "<div style='height: 10vw; margin: 10px auto 0 auto; width: 10vw;'>				<img style='height: 100%; width: 100%;' src='" + os.getenv("CLIENT_URL") + "/favicon.ico'/>			</div><h3 style='color: grey; text-align: center;'>BetaRush</h3>		</div>		"
		html += "<div style='color: black; font-size: 20px; font-weight: bold; margin: 0 10%; text-align: center;'>			"
		html += "Yay! Someone is currently trying out your product, " + product["name"]
		html += "</div>		<div style='display: flex; flex-direction: row; justify-content: space-around; width: 100%;'>			"
		html += "</div>	</div></body></html>"

		send_email(creator["email"], "A customer is trying our your product", html)

		if testing == None:
			query("insert into product_testing (testerId, productId, advice) values (" + userId + ", " + productId + ", '')")
		else:
			query("update product_testing set advice = '' where id = " + str(testing["id"]))

		return { "msg": "" }
	elif user["isBanned"] == 1:
		return { "banned": True }

	return { "status": "nonExist" }, 400

@app.route("/get_feedbacks", methods=["POST"])
def get_feedbacks():
	content = request.get_json()

	userId = str(content['userId'])
	offset = content['offset']

	sql = "select * from product where creatorId = " + userId
	sql += " and id in ("
	sql += "select productId from product_testing where not advice = '' and ("
	sql += "select count(*) from tester_rate where productId = product_testing.productId and testerId = product_testing.testerId and testingId = product_testing.id"
	sql += ") = 0"
	sql += ")"
	sql += " limit " + str(offset) + ", 10"

	datas = query(sql, True).fetchall()
	products = []

	for data in datas:
		feedbacks = query("select id, advice, testerId from product_testing where productId = " + str(data["id"]), True).fetchall()
		otherInfo = json.loads(data["otherInfo"])

		for info in feedbacks:
			info["key"] = "advice-" + str(data["id"]) + "-" + str(info["id"])

		products.append({
			**data,
			"key": "product-" + str(data["id"]),
			"name": data["name"],
			"image": json.loads(data["image"]),
			"feedbacks": feedbacks,
			"deposited": True if otherInfo["charge"] != "" else False
		})

	return { "products": products, "offset": len(datas) + offset }

@app.route("/get_product_feedbacks", methods=["POST"])
def get_product_feedbacks():
	content = request.get_json()

	productId = str(content['productId'])

	sql = "select id, advice, testerId from product_testing where productId = " + productId + " and ("
	sql += "select count(*) from tester_rate where testerId = product_testing.testerId and productId = product_testing.productId and testingId = product_testing.id"
	sql += ") = 0"
	feedbacks = query(sql, True).fetchall()
	product = query("select name, image, otherInfo from product where id = " + productId, True).fetchone()

	otherInfo = json.loads(product["otherInfo"])

	for info in feedbacks:
		info["key"] = "feedback-" + str(info["id"])

	return { 
		"feedbacks": feedbacks, 
		"name": product["name"], 
		"logo": json.loads(product["image"]),
		"deposited": otherInfo["charge"] != ""
	}

