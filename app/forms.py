from flask_wtf import FlaskForm

from wtforms import StringField, BooleanField, validators

from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
	openid = StringField('openid', validators=[DataRequired()])
	remember_me = BooleanField('remember_me', default=False)

class AboutMe(FlaskForm):
	aboutme = StringField('aboutme', validators=[DataRequired()])

class PostSomething(FlaskForm):
	post = StringField('post', validators=[DataRequired()])

class SearchForm(FlaskForm):
	search = StringField('search', validators=[DataRequired()])