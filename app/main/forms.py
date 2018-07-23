from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, IPAddress
from wtforms import ValidationError


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EditProfileForm(FlaskForm):
    ip = StringField('设备地址', validators=[DataRequired(), Length(1, 15),IPAddress(ipv4=True, ipv6=False)])
    port = StringField('端口号',validators=[DataRequired()])
    timeval = StringField('采样间隔')
    cnt = StringField('采样点数')
    submit = SubmitField('连接设备')

class PerfForm(FlaskForm):
    hz = StringField('采样频率*',validators=[DataRequired()])
    time = StringField('采样时间(单位:秒)')
    cpu = StringField('监控cpu(需要监控多个cpu的话用逗号隔开)')
    pid = StringField('监控进程pid')
    adv = StringField('高级参数')
    #submit = SubmitField('开始采样')

class FuncForm(FlaskForm):
    func = StringField('函数*',validators=[DataRequired()])
    depth = StringField('深度')
    #submit = SubmitField('开始采样')