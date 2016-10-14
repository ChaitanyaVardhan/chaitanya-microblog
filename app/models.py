from hashlib import md5

from app import db

from app import app

import flask_whooshalchemy as whooshalchemy

followers = db.Table('followers', 
	db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
	)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nickname = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	aboutme = db.Column(db.Text(250))
	last_seen = db.Column(db.DateTime)
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	followed = db.relationship('User', 
								secondary=followers,
								primaryjoin=(followers.c.follower_id == id),
								secondaryjoin=(followers.c.followed_id == id),
								backref = db.backref('followers', lazy='dynamic'),
								lazy='dynamic' )
	@property 
	def is_authenticated(self):
		return True

	@property 
	def is_active(self):
		return True

	@property 
	def is_anonymous(self):
		return False

	def get_id(self):
		try:
			return unicode(self.id)
		except NameError:
			return str(self.id)

	def avatar(self, size):
		return 'https://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)

	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)
			return self

	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)
			return self

	def is_following(self, user):
		return self.followed.filter(followers.c.followed_id == user.id).count() > 0

	'''
	def followed_posts(self):
		posts = []
		post = {
				'author': { 'nickname': ''},
				'body': ''
			}
		bodies = []
		for entry in self.followed:
			post['author']['nickname'] = entry.nickname
			allposts = Post.query.filter_by(user_id=entry.id)
			post['body'] = allposts[0].body
			posts.append(post)
			post['body'] = allposts[1].body
			posts.append(post)
			post['body'] = allposts[2].body
			posts.append(post)
			post['body'] = allposts[3].body
			posts.append(post)
		return posts
	'''
	def followed_posts(self):
		return Post.query.join(followers, (followers.c.follower_id == self.id)).filter(Post.user_id == followers.c.followed_id).order_by(Post.timestamp.desc())

	def __repr__(self):
		return '<User %r>' % (self.nickname)

class Post(db.Model):
	__searchable__ = ['body']
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Post %r>'% (self.body)

whooshalchemy.whoosh_index(app, Post)