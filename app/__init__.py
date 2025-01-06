from flask import Flask
from app.routes.googlemap_route import googlemap_route

def create_app():
    app = Flask(__name__)
    # app.config.from_object('config') 

    app.register_blueprint(googlemap_route, url_prefix='/googlemap')

    return app
