import pymysql.cursors, os, json
from random import randint
from time import time
from config import *
import stripe, requests
import numpy as np

stripe.api_key = os.getenv("STRIPE_KEY")

photoUrl = os.getenv("PHOTO_URL")
launchAmount = 10.00
regainAmount = 10.00
appFee = 5
pending = False

def query(sql, output = False):
	db_host = str(os.getenv("DB_HOST"))
	user = str(os.getenv("USER"))
	password = str(os.getenv("PASS"))
	db_name = str(os.getenv("DB"))

	dbconn = pymysql.connect(
		host=db_host, user="geottuse",
		password=password, db=db_name,
		charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, 
		autocommit=True
	)
	cursorobj = dbconn.cursor()
	cursorobj.execute(sql)

	dbconn.close()

	if output == True:
		return cursorobj

def getId():
	letters = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", 
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"
	]
	char = ""

	while True:
		char = ""

		for k in range(randint(10, 20)):
			char += str(randint(0, 9)) if randint(0, 9) % 2 == 0 else (letters[randint(0, 25)]).upper()

		num = 0

		if num == 0:
			break
	        
	return char

def get_stripe_fee(chargeInfo, amount):
	currency = chargeInfo["currency"]
	country = chargeInfo["country"]

	percent = (2.9 + (0.2 if currency != "cad" else 0) + (0.8 if country != "CA" else 0)) / 100

	fee = np.round((amount * percent + 0.3), 2)

	return amount - fee

def get_balance():
	info = stripe.Balance.retrieve()

	return info.available[0].amount

def send_email(receiver, subject, html):
	try:
		payload = """
			{
				\"from\": { \"address\": \"admin@geottuse.com\"},
				\"to\": [
					{\"email_address\": {\
						"address\": \"""" + receiver + """\",
						\"name\": \"""" + subject + """\"
					}}
				],
				\"subject\":\"Waver\",
				\"htmlbody\":\"""" + html + """\"\n
			}
		"""

		headers = {
			'accept': "application/json",
			'content-type': "application/json",
			'authorization': "Zoho-enczapikey wSsVR60jrx70XKwszmWqIOo5m15RA1+gRhh8igby6SX7Ta2U8Mc8khfHB1CnSvIZGWRuRmdAorp6zh4F2zEI2oslmVoDASiF9mqRe1U4J3x17qnvhDzKXm1fmhOPLY0BwQ9sm2dlFMgk+g==",
		}

		response = requests.request("POST", "https://api.zeptomail.com/v1.1/email", data=payload, headers=headers)

		print(response.text)
	except Exception as error:
		print("error sending email", error)
