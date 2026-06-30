from flask import Flask
from config import Config
from auth.routes import auth_bp
from bewertungen.routes import bewertungen_bp
#from themen.routes import themen_bp
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.register_blueprint(auth_bp)
app.register_blueprint(bewertungen_bp)
#app.register_blueprint(themen_bp)

if __name__ == '__main__':
    app.run()
