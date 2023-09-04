from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.serving import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.shared_data import SharedDataMiddleware

from controllers.user import app as user_controller
from controllers.product import app as product_controller
from models import *
from config import *

db_host = str(os.getenv("DB_HOST"))
user = str(os.getenv("USER"))
password = str(os.getenv("PASS"))
db_name = str(os.getenv("DB"))
mysql_str = 'mysql://geottuse:G3ottu53?@localhost/getstartupfeedback'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = mysql_str
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['MYSQL_HOST'] = db_host
app.config['MYSQL_USER'] = user
app.config['MYSQL_PASSWORD'] = password
app.config['MYSQL_DB'] = db_name

db.init_app(app)
migrate = Migrate(app, db, compare_type=True)

app.wsgi_app = DispatcherMiddleware(None, {
	'/flask/user': user_controller,
	'/flask/product': product_controller
})

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
	'/flask/static': os.path.join(os.path.dirname(__file__), 'static')
})

if __name__ == "__main__":
	run_simple(str(os.getenv("HOST")), int(os.getenv("PORT")), app, use_reloader=True, use_debugger=True, use_evalex=True)
