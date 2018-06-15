#!/usr/bin/env python3
import os
from app import create_app
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell

app = create_app('default')
manager = Manager(app) #为flask框架提供命令行支持
#migrate = Migrate(app, db)

def make_shell_context():#导入实例和模型
    return dict(app=app, db=db)
manager.add_command("shell",Shell(make_context=make_shell_context))#挂接回调函数用于建立shell的上下文
manager.add_command('db', MigrateCommand) #用于支持命令行db操作

if __name__ == '__main__':
    manager.run()