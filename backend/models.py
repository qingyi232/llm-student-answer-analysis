from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    real_name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin / teacher / student
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.String(500))
    student_no = db.Column(db.String(30))
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'role': self.role,
            'email': self.email,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'student_no': self.student_no,
            'department': self.department,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(50))
    cover_url = db.Column(db.String(500))
    student_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    teacher = db.relationship('User', backref='courses')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.real_name if self.teacher else '',
            'description': self.description,
            'subject': self.subject,
            'cover_url': self.cover_url,
            'student_count': self.student_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class CourseStudent(db.Model):
    __tablename__ = 'course_students'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.now)

    course = db.relationship('Course', backref='enrollments')
    student = db.relationship('User', backref='enrollments')


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), nullable=False)  # 论述题/简答题/案例分析题
    subject = db.Column(db.String(50))
    reference_answer = db.Column(db.Text)
    grading_criteria = db.Column(db.Text)
    max_score = db.Column(db.Float, default=10.0)
    knowledge_points = db.Column(db.Text)  # JSON array
    difficulty = db.Column(db.String(10), default='中等')  # 简单/中等/困难
    created_at = db.Column(db.DateTime, default=datetime.now)

    course = db.relationship('Course', backref='questions')
    teacher = db.relationship('User', backref='questions')

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else '',
            'teacher_id': self.teacher_id,
            'title': self.title,
            'content': self.content,
            'question_type': self.question_type,
            'subject': self.subject,
            'reference_answer': self.reference_answer,
            'grading_criteria': self.grading_criteria,
            'max_score': self.max_score,
            'knowledge_points': json.loads(self.knowledge_points) if self.knowledge_points else [],
            'difficulty': self.difficulty,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # draft/active/closed
    created_at = db.Column(db.DateTime, default=datetime.now)

    course = db.relationship('Course', backref='assignments')

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else '',
            'title': self.title,
            'description': self.description,
            'deadline': self.deadline.strftime('%Y-%m-%d %H:%M:%S') if self.deadline else None,
            'status': self.status,
            'question_count': len(self.assignment_questions),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class AssignmentQuestion(db.Model):
    __tablename__ = 'assignment_questions'
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    order_num = db.Column(db.Integer, default=1)
    score_weight = db.Column(db.Float, default=1.0)

    assignment = db.relationship('Assignment', backref='assignment_questions')
    question = db.relationship('Question', backref='assignment_questions')


class StudentAnswer(db.Model):
    __tablename__ = 'student_answers'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    answer_content = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer, default=0)
    submit_time = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='submitted')  # submitted/analyzing/completed

    student = db.relationship('User', backref='answers')
    question = db.relationship('Question', backref='student_answers')
    assignment = db.relationship('Assignment', backref='student_answers')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.real_name if self.student else '',
            'student_no': self.student.student_no if self.student else '',
            'question_id': self.question_id,
            'question_title': self.question.title if self.question else '',
            'assignment_id': self.assignment_id,
            'answer_content': self.answer_content,
            'word_count': self.word_count,
            'submit_time': self.submit_time.strftime('%Y-%m-%d %H:%M:%S') if self.submit_time else None,
            'status': self.status
        }


class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('student_answers.id'), nullable=False)
    overall_score = db.Column(db.Float, nullable=False)
    knowledge_score = db.Column(db.Float)
    logic_score = db.Column(db.Float)
    expression_score = db.Column(db.Float)
    knowledge_details = db.Column(db.Text)  # JSON
    logic_details = db.Column(db.Text)      # JSON
    expression_details = db.Column(db.Text)  # JSON
    error_points = db.Column(db.Text)        # JSON
    highlights = db.Column(db.Text)          # JSON
    analysis_time_ms = db.Column(db.Integer)
    model_used = db.Column(db.String(50), default='CASA-v1')
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer = db.relationship('StudentAnswer', backref='analysis_results')

    def to_dict(self):
        return {
            'id': self.id,
            'answer_id': self.answer_id,
            'overall_score': self.overall_score,
            'knowledge_score': self.knowledge_score,
            'logic_score': self.logic_score,
            'expression_score': self.expression_score,
            'knowledge_details': json.loads(self.knowledge_details) if self.knowledge_details else {},
            'logic_details': json.loads(self.logic_details) if self.logic_details else {},
            'expression_details': json.loads(self.expression_details) if self.expression_details else {},
            'error_points': json.loads(self.error_points) if self.error_points else [],
            'highlights': json.loads(self.highlights) if self.highlights else [],
            'analysis_time_ms': self.analysis_time_ms,
            'model_used': self.model_used,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analysis_results.id'), nullable=False)
    overall_feedback = db.Column(db.Text)
    strengths = db.Column(db.Text)               # JSON array
    weaknesses = db.Column(db.Text)               # JSON array
    improvement_suggestions = db.Column(db.Text)  # JSON array
    recommended_resources = db.Column(db.Text)    # JSON array
    study_tips = db.Column(db.Text)
    teacher_comment = db.Column(db.Text)
    teacher_score_adjustment = db.Column(db.Float, default=0)
    is_teacher_reviewed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    analysis = db.relationship('AnalysisResult', backref='feedbacks')

    def to_dict(self):
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'overall_feedback': self.overall_feedback,
            'strengths': json.loads(self.strengths) if self.strengths else [],
            'weaknesses': json.loads(self.weaknesses) if self.weaknesses else [],
            'improvement_suggestions': json.loads(self.improvement_suggestions) if self.improvement_suggestions else [],
            'recommended_resources': json.loads(self.recommended_resources) if self.recommended_resources else [],
            'study_tips': self.study_tips,
            'teacher_comment': self.teacher_comment,
            'teacher_score_adjustment': self.teacher_score_adjustment,
            'is_teacher_reviewed': self.is_teacher_reviewed,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
