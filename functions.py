import pymysql.cursors, os, json
from random import randint
from time import time
from config import *
import stripe

stripe.api_key = "sk_test_51NmA1PFqjgkiO0WHxOmFjOzgwHorLyTxjyWJ926HiBK10KHnTnh7q8skEmQ5c0NpHxI3mk2fbejMASjazhPlmGkv00L98uIq8G"

photoUrl = os.getenv("PHOTO_URL")

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
