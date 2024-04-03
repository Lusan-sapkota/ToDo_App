from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'SuperSecretKey'
login_manager = LoginManager()
login_manager.init_app(app)
# Create the 'database' directory if it doesn't exist
if not os.path.exists('database'):
    os.makedirs('database')

# Set the database URI
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database', 'todo.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30), unique=True, nullable=False)
    lastname = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    subscribe = db.Column(db.Boolean, default=False)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(9999), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # No foreign key constraint

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signin', methods=['GET', 'POST'])
def signIn():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # User is logged in successfully!
            login_user(user)  # Login the user
            return redirect(url_for('todos'))
        else:
            return 'Invalid email or password', 401
    else:
        return render_template('login.html')
    
@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    if request.method == 'POST':
        # Get form data
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        gender = request.form.get('gender')
        subscribe = 'subscribe' in request.form

        if password is None:
            return 'Please enter a password', 400
        # Hash the password for security
        password_hash = generate_password_hash(password)

        # Create a new user
        user = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            password=password_hash,
            gender=gender,
            subscribe=subscribe
        )

        # Add the new user to the database
        db.session.add(user)
        db.session.commit()

        # User is registered and can be logged in now!
        login_user(user)  # Login the user
        return redirect(url_for('todos'))
    else:
        return render_template('register.html')


@app.route('/logOut')
def logOut():
    logout_user()  # Logout the user
    return render_template('index.html')

@app.route('/todos', methods=['GET', 'POST'])
@login_required  # Ensure the user is logged in before accessing this route
def todos():
    if request.method == 'POST':
        task = request.form.get('task')
        time_str = request.form.get('time')
        time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S') if time_str else datetime.now()
        time = time.replace(microsecond=0)
        # Use current_user.id to associate the todo with the logged-in user
        todo = Todo(task=task, time=time, user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()

    # Fetch todos associated with the logged-in user only
    todos = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('list.html', todos=todos, firstname=current_user.firstname)

@app.route('/update_todo/<int:id>', methods=['POST'])
def update_todo(id):
    new_task = request.form.get('task')
    todo = Todo.query.get(id)
    todo.task = new_task
    db.session.commit()
    return redirect(url_for('todos'))

@app.route('/delete_todo/<int:id>', methods=['POST'])
def delete_todo(id):
    todo = Todo.query.get(id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('todos'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
