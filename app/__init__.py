from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

bootstrap = Bootstrap()
moment = Moment()
#db = SQLAlchemy()
app = Flask(__name__)

#使用工厂函数，启动时再创建app
def create_app():

    app.debug = True
    
    bootstrap.init_app(app)
    moment.init_app(app)
    #db.init_app(app)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint) #注册蓝本时，蓝本里的路由才生效。这是主页蓝本

    return app
