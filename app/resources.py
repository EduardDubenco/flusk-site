from flask import request
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models import Task, User
from .extensions import db

class TaskResource(Resource):
    @jwt_required()
    def get(self, task_id):
        task = Task.query.get_or_404(task_id)
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': task.completed
        }

    @jwt_required()
    def put(self, task_id):
        data = request.get_json()
        task = Task.query.get_or_404(task_id)
        task.title = data['title']
        task.description = data['description']
        task.completed = data['completed']
        db.session.commit()
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': task.completed
        }

    @jwt_required()
    def delete(self, task_id):
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return {'message': 'Task deleted'}

class TaskListResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        tasks = Task.query.filter_by(user_id=user_id).all()
        return [{'id': task.id, 'title': task.title, 'description': task.description, 'completed': task.completed} for task in tasks]

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json()
        task = Task(title=data['title'], description=data['description'], completed=data['completed'], user_id=user_id)
        db.session.add(task)
        db.session.commit()
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': task.completed
        }, 201

class UserLoginResource(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=user.id)
            return {'access_token': access_token}
        return {'message': 'Invalid credentials'}, 401
