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