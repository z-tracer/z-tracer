from flask import Flask
from flask_bootstrap import Bootstrap
from config import config
#from flask_sqlalchemy import SQLAlchemy

from .flamescope.views.stack import MOD_STACK
from .flamescope.views.heatmap import MOD_HEATMAP

bootstrap = Bootstrap()
#db = SQLAlchemy()
app = Flask(__name__)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name]) 
    config[config_name].init_app(app)
    
    bootstrap.init_app(app)
    #db.init_app(app)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    app.register_blueprint(MOD_STACK)
    app.register_blueprint(MOD_HEATMAP)
    
    return app
