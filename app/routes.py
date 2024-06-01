from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_restful import Api
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from .models import User, Task, Post, Comment
from .extensions import db, login_manager
from .resources import TaskResource, TaskListResource, UserLoginResource
import sqlalchemy

main_bp = Blueprint('main', __name__)
api = Api(main_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=5, error_out=False)
    return render_template('index.html', posts=posts)

@main_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('You need to be logged in to comment')
            return redirect(url_for('main.login'))
        comment_body = request.form.get('comment')
        comment = Comment(body=comment_body, post_id=post_id, user_id=current_user.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added')
        return redirect(url_for('main.post', post_id=post_id))
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.asc()).all()
    return render_template('post.html', post=post, comments=comments)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or email already exists.')
            return redirect(url_for('main.register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash('Invalid email or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=request.form.get('remember'))
        return redirect(url_for('main.index'))
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_bp.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        post = Post(title=title, body=body, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!')
        return redirect(url_for('main.index'))
    return render_template('create_post.html')

@main_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    results = Post.query.filter(
        sqlalchemy.or_(
            Post.title.ilike(f'%{query}%'),
            Post.body.ilike(f'%{query}%')
        )
    ).paginate(page=page, per_page=5, error_out=False)
    return render_template('search_results.html', query=query, results=results)

@main_bp.route('/tasks', methods=['GET'])
@login_required
def tasks():
    user_id = current_user.id
    tasks = Task.query.filter_by(user_id=user_id).all()
    return render_template('tasks.html', tasks=tasks)

@main_bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        task = Task(title=title, description=description, user_id=current_user.id)
        db.session.add(task)
        db.session.commit()
        flash('Your task has been created!')
        return redirect(url_for('main.tasks'))
    return render_template('create_task.html')

@main_bp.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You are not authorized to delete this task.')
        return redirect(url_for('main.tasks'))
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.')
    return redirect(url_for('main.tasks'))

@main_bp.route('/tasks/toggle_complete/<int:task_id>', methods=['POST'])
@login_required
def toggle_complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You are not authorized to modify this task.')
        return redirect(url_for('main.tasks'))
    task.completed = not task.completed
    db.session.commit()
    flash('Task status updated.')
    return redirect(url_for('main.tasks'))

# Register API resources
api.add_resource(TaskListResource, '/api/tasks')
api.add_resource(TaskResource, '/api/tasks/<int:task_id>')
api.add_resource(UserLoginResource, '/api/login')
