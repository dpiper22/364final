#SI364 Final Project Setup code
#By: David Piper

#imports
import os
import requests
import json
#from giphy_api_key import api_key
from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.debug = True
app.use_reloader = True
app.config['SECRET_KEY'] = 'hardtoguessstring'
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/SI364FinalDJPIPER" # TODO 364: You should edit this to correspond to the database name YOURUNIQNAMEHW4db and create the database of that name (with whatever your uniqname is; for example, my database would be jczettaHW4db). You may also need to edit the database URL further if your computer requires a password for you to run this.
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)

##Association Tables##

actor_collection = db.Table('actor_collection', db.Column('actors', db.Integer, db.ForeignKey('Movies.id')), db.Column('collection_id', db.Integer, db.ForeignKey('FavoriteActorsCollection.id')))

###MODELS####

class User(UserMixin, db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    actors = db.relationship('FavoriteActorsCollection', backref = 'User')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#model to store movie searches

class Movies(db.Model):
    __tablename__ = "Movies"
    id = db.Column(db.Integer, primary_key=True)
    movie = db.Column(db.String(128))
    actors = db.Column(db.String(256))
    rating = db.Column(db.String(4))

    
    def __repr__(self):
        return "Movie: {}, Actors: {}, Rating: {}".format(self.movie, self.actors, self.rating)



#model to store movie actors
class FavoriteActorsCollection(db.Model):
	__tablename__ = "FavoriteActorsCollection"
	id = db.Column(db.Integer, primary_key= True)
	name = db.Column(db.String(255))
	user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
#one to many relationship with user model and multiple favorite actors in each collection and many to many relationship with multiple actors in multiple movies
	actors = db.relationship('Movies', secondary= actor_collection, backref = db.backref('FavoriteActorsCollection', lazy='dynamic'), lazy='dynamic')


###FORMS###

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


#models to search for movies

class MovieSearchForm(FlaskForm):
    search = StringField("Enter one of your favorite movies to find out the actors and rating!", validators=[Required()])
    submit = SubmitField('Submit')

class FavMovieActorsForm(FlaskForm):
    name = StringField('Enter a name for your collection of actors', validators=[Required()])
    choose_actors = SelectMultipleField('Cast of actors to include in collection')
    submit = SubmitField('Create your collection')

class UpdateButtonForm(FlaskForm):
    new_movie = StringField("Enter updated name of movie", validators=[Required()])
    submit = SubmitField('Update')

class DeleteButtonForm(FlaskForm):
    submit = SubmitField('Delete')

##Helper Functions##
def get_movies_from_tmbd(search):
    """ Returns data from themoviedb API with a list of the actors in the movie and the rating of the movie """
    baseurl = "https://api.themoviedb.org/3/search/movie?api_key=60323ac7413f9036e9c5ea5559462753&language=en-US&query={}&page=1&include_adult=false".format(search)
    req = requests.get(baseurl).text
    json_d = json.loads(req)
    return json_d
    #movie_id = json_d['results'][0]['id']
    #a_url = "https://api.themoviedb.org/3/movie/{}/credits?api_key=60323ac7413f9036e9c5ea5559462753".format(movie_id)
    #req_a = requests.get(a_url).text
    #json_a = json.loads(req_a)
    #actors = {}
    #for x in range(5):
    #actor = (json_a['cast'][x]['name'])
    #character = (json_a['cast'][x]['character'])
    # actors[actor] = character

    #return json_d['results'][0]['original_title'], json_d['results'][0]['vote_average'], actors)

def get_movies_actors(search):
    baseurl = "https://api.themoviedb.org/3/search/movie?api_key=60323ac7413f9036e9c5ea5559462753&language=en-US&query={}&page=1&include_adult=false".format(search)
    req = requests.get(baseurl).text
    json_d = json.loads(req)
    movie_id = json_d['results'][0]['id']
    a_url = "https://api.themoviedb.org/3/movie/{}/credits?api_key=60323ac7413f9036e9c5ea5559462753".format(movie_id)
    req_a = requests.get(a_url).text
    json_a = json.loads(req_a)
    actors = []
    for x in range(5):
        actors.append(json_a['cast'][x]['name'])
    return actors


def get_movie_id(id):
    """ Should return movie object or none """
    m = Movies.query.filter_by(id=id).first()
    return m

def get_or_create_movie(title, url):
    mvs = Movies.query.filter_by(movie= movie).first()
    if mvs:
        return mvs
    else:
        mvs = Movies(movie=movie, embedURL=url)
        db.session.add(mvs)
        db.session.commit()
        return mvs

def get_actor_id(id):
    """Sould return actor object or none"""
    a = Movies.query.filter_by(id=id).first()
    return a

def get_or_create_fav_actors(names, current_user, actor_list=[]):
    """ Always return a FavoriteActorsCollection instance"""
    fac = FavoriteActorsCollection.query.filter_by(name=names, user_id=current_user.id).first()
    if fac:
        return fac
    else:
        fac = FavoriteActorsCollection(name=names, user_id=current_user.id)
        for f in actor_list:
            fac.actors.append(f)
        db.session.add(fac)
        db.session.commit()
        return fac



##Routes##

## Error Handling Routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


## Routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now log in!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)
#from hw4
@app.route('/secret')
@login_required
def secret():
	return "Only authenticated users can do this! Please login or contact the site admin."
#view function to render movie serch form
@app.route('/', methods=['GET', 'POST'])
def index():
    form = MovieSearchForm()
    if form.validate_on_submit():
        movie = form.search.data
        m = Movies.query.filter_by(movie = movie).first()
        if m:
            movie_name = m.movie
            rat = m.rating
            actors = m.actors
            return redirect(url_for('movie_info'))
        else:
            json = get_movies_from_tmbd(movie)
            cast_list = get_movies_actors(movie)
            movie_name = json['results'][0]['original_title']
            rat = json['results'][0]['vote_average']
            actors = ', '.join(cast_list)
            actor_string = str(actors)
            m_info = Movies(movie = movie_name, rating = rat, actors= actor_string)
            db.session.add(m_info)
            db.session.commit()
            return redirect(url_for('movie_info'))
    return render_template('index.html', form=form)

#view function to view movie searches
@app.route('/movie_searches')
def movie_searches():
    form = UpdateButtonForm()
    form_d = DeleteButtonForm()
    movies = Movies.query.all()
    return render_template('movie_searches.html', all_movies = movies, form=form, form_d=form_d)




@app.route('/search_movie')
def search_movie():
    form = MovieSearchForm()
    return render_template('search_movie.html', form=form)

#view function to view movie searched and rating
@app.route('/movie_info')
def movie_info():
    db_movie = Movies.query.all()
    movie = ""
    rating = ""
    actors = ""
    for movs in db_movie:
        movie = movs.movie
        rating = movs.rating
        actors = movs.actors
    return render_template("movie_info.html", movie=movie, rating=rating, actors=actors)


@app.route('/create_collection', methods=["GET", "POST"])
@login_required
def create_collection():
    form = FavMovieActorsForm()
    actrs = Movies.query.all()
    choices = [(a.id, a.actors) for a in actrs]
    form.choose_actors.choices = choices
    if request.method == 'POST':
        pick_actors = form.choose_actors.data
        actor_obj = [get_actor_id(int(id)) for id in pick_actors]
        get_or_create_fav_actors(names=form.name.data, current_user=current_user, actor_list= actor_obj)
        return redirect(url_for('collections'))
    return render_template('create_collection.html', form=form)

@app.route('/collections', methods= ["GET", "POST"])
@login_required
def collections():
    collections = FavoriteActorsCollection.query.filter_by(user_id=current_user.id).all()
    return render_template('collections.html', collections=collections)

@app.route('/delete/<movie_d>', methods= ["POST", "GET"])
def delete(movie_d):
    delete_lst = Movies.query.filter_by(movie=movie_d).first()
    if delete_lst:
        db.session.delete(delete_lst)
        flash('Deleted Movie Data: {}'.format(delete_lst.movie))
    return redirect(url_for('index'))

@app.route('/update/<lst>', methods= ["POST", "GET"])
def update(lst):
    form = UpdateButtonForm()
    if form.validate_on_submit():
        new_movie = form.new_movie.data
        mov = Movies.query.filter_by(movie=lst).first()
        mov.movie = new_movie
        db.session.commit()
        flash('Updated movie: {}'.format(new_movie))
        return redirect(url_for('movie_searches'))
    return render_template('update.html', lst = lst, form=form)

#used some work from HW4
@app.route('/collection/<id_num>')
def single_collection(id_num):
    id_num = int(id_num)
    collection = FavoriteActorsCollection.query.filter_by(id=id_num).first()
    actors = collection.actors.all()
    return render_template('collection.html', collection=collection, actors=actors)


#view function to view the actors in a movie



if __name__ == '__main__':
    db.create_all()
    manager.run()



