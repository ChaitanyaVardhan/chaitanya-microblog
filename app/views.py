from flask import render_template, flash, redirect, g, session, url_for, request

from flask_login import current_user, login_required, login_user, logout_user

from datetime import datetime

from app import app, db, lm, oid

from .forms import LoginForm, AboutMe, PostSomething, SearchForm

from .models import User, Post

from .emails import follower_notification

from config import POSTS_PER_PAGE

from config import MAX_SEARCH_RESULTS

from .momentjs import momentjs

app.jinja_env.globals['momentjs'] = momentjs

#user loader callback
#write a function that loads a user from the database
#the load_user function is registered with Flask-Login through the decorator lm.user_loader
@lm.user_loader
def load_user(id):
	return User.query.get(int(id))

@app.before_request
def before_request():
	g.user = current_user
	if g.user.is_authenticated:
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()
		g.search_form = SearchForm()

@app.after_request
def after_request(response):
	db.session.remove()	
	return response

@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
def index(page=1):
	user = g.user
	form = PostSomething()
	if form.validate_on_submit():
		post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
		db.session.add(post)
		db.session.commit()
		flash('Your post is now live')
		return redirect(url_for('index'))
	posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
	return render_template('index.html', user=user, form=form, title='Home', posts=posts)

#write a function that shows the login page
#oid.loginhandler tells Flask-OpenID that this is our login view function
@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
	if g.user is not None and g.user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.openid.data is not None:
		session['remember_me'] = form.remember_me.data
		return oid.try_login(form.openid.data, ask_for=['email', 'nickname'])

	return render_template('login.html',
							 title='Sign In',
							  form=form, 
							  providers=app.config['OPENID_PROVIDERS'])

#Flask-OpenID will call this function that is registered with oid.after_login decorator
@oid.after_login
def after_login(resp):
	if resp.email is None or resp.email == "":
		flash('Invalid login. Please try again')
		return redirect(url_for('login'))
	user = User.query.filter_by(email=resp.email).first()	
	if user is None:
		nickname = resp.nickname
		if nickname is None or nickname == "":
			nickname = resp.email.split('@')[0]
		user = User(nickname=nickname, email=resp.email)
		db.session.add(user)
		db.session.commit()
	remember_me = False
	if 'remember_me' in session:
		remember_me = session['remember_me']
		session.pop('remember_me', None)
	login_user(user, remember=remember_me)
	return redirect(request.args.get('next') or url_for('index'))

#write the function to logout user
@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

#write the view function for user profile
@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
	user = User.query.filter_by(nickname=nickname).first()
	if user == None:
		flash('User %s not found' % nickname)
		return redirect(url_for('index'))
	posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, POSTS_PER_PAGE, False)
	return render_template('user.html', user=user, posts=posts)

@app.route('/edit_about_me', methods=["GET", "POST"])
def edit_about_me():
	form = AboutMe()
	if form.aboutme.data:
		g.user.aboutme = form.aboutme.data
		db.session.add(g.user)
		db.session.commit()
		flash("Your messages have been saved")
		return redirect(url_for('edit_about_me'))
	else:
		form.aboutme.data = g.user.aboutme

	return render_template('aboutme.html', form=form)

@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
	user = User.query.filter_by(nickname=nickname).first()
	if user is None:
		flash('User %s not found' %nickname)
		return redirect(url_for('index'))
	if user == g.user:
		flash('You can\'t follow yourself!')
		return redirect(url_for('user', nickname=nickname))
	u = g.user.follow(user)
	if u is None:
		flash('Cannot follow ' + nickname + '.')
		return redirect(url_for('user', nickname=nickname))
	db.session.add(u)
	db.session.commit()
	flash('You are now following ' + nickname + '!')
	follower_notification(user, g.user)
	return redirect(url_for('user', nickname=nickname))
	
@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
	user = User.query.filter_by(nickname=nickname).first()
	if user is None:
		flash('User ' + nickname + ' not found')
		return redirect(url_for('index'))
	if user == g.user:
		flash('You can\'t unfollow yourself!')
		return redirect(url_for('user', nickname=nickname))
	u = g.user.unfollow(user)
	if u is None:
		flash('Cannot unfollow ' + nickname + '.')
		return redirect(url_for('user', nickname=nickname))
	db.session.add(u)
	db.session.commit()
	flash ('You have Unfollowed ' + nickname + '.')
	return redirect(url_for('user', nickname=nickname))

@app.route('/search', methods=['POST'])
@login_required
def search():
	if not g.search_form.validate():
		return redirect(url_for('index'))
	return redirect(url_for('search_results', query=g.search_form.search.data))

@app.route('/search_results/<query>', methods=['GET'])
@login_required
def search_results(query):
	results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
	return render_template('search_results.html', query=query, results=results)
