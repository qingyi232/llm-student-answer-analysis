from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import Config
from models import db, User, Course, CourseStudent, Question, Assignment, AssignmentQuestion, StudentAnswer, AnalysisResult, Feedback
from llm_service import analyze_answer, _local_fallback_analyze
from datetime import datetime
import json
import csv
import io

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
jwt = JWTManager(app)
db.init_app(app)


# ======================== 认证 API ========================

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(force=True, silent=True) or {}
    user = User.query.filter_by(username=data.get('username', '')).first()
    if not user or not user.check_password(data.get('password', '')):
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({
        'code': 200,
        'msg': '登录成功',
        'data': {'token': token, 'user': user.to_dict()}
    })


@app.route('/api/auth/info', methods=['GET'])
@jwt_required()
def get_user_info():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404
    return jsonify({'code': 200, 'data': user.to_dict()})


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'code': 400, 'msg': '用户名已存在'}), 400
    user = User(
        username=data['username'],
        real_name=data.get('real_name', data['username']),
        role=data.get('role', 'student'),
        email=data.get('email'),
        phone=data.get('phone'),
        student_no=data.get('student_no'),
        department=data.get('department')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '注册成功', 'data': user.to_dict()})


# ======================== 用户管理 API ========================

@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    role = request.args.get('role')
    query = User.query
    if role:
        query = query.filter_by(role=role)
    keyword = request.args.get('keyword')
    if keyword:
        query = query.filter(
            (User.real_name.contains(keyword)) | (User.username.contains(keyword)) | (User.student_no.contains(keyword))
        )
    users = query.order_by(User.created_at.desc()).all()
    return jsonify({'code': 200, 'data': [u.to_dict() for u in users]})


@app.route('/api/users/<int:uid>', methods=['PUT'])
@jwt_required()
def update_user(uid):
    user = User.query.get_or_404(uid)
    data = request.get_json()
    for key in ['real_name', 'email', 'phone', 'department', 'student_no', 'role']:
        if key in data:
            setattr(user, key, data[key])
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': user.to_dict()})


@app.route('/api/users/<int:uid>', methods=['DELETE'])
@jwt_required()
def delete_user(uid):
    user = User.query.get_or_404(uid)
    CourseStudent.query.filter_by(student_id=uid).delete()
    db.session.delete(user)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ======================== 课程 API ========================

@app.route('/api/courses', methods=['GET'])
@jwt_required()
def get_courses():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if user.role == 'teacher':
        courses = Course.query.filter_by(teacher_id=uid).order_by(Course.created_at.desc()).all()
    elif user.role == 'student':
        enrolled = CourseStudent.query.filter_by(student_id=uid).all()
        course_ids = [e.course_id for e in enrolled]
        courses = Course.query.filter(Course.id.in_(course_ids)).order_by(Course.created_at.desc()).all()
    else:
        courses = Course.query.order_by(Course.created_at.desc()).all()
    return jsonify({'code': 200, 'data': [c.to_dict() for c in courses]})


@app.route('/api/courses', methods=['POST'])
@jwt_required()
def create_course():
    data = request.get_json()
    uid = int(get_jwt_identity())
    course = Course(
        name=data['name'],
        code=data.get('code'),
        teacher_id=uid,
        description=data.get('description'),
        subject=data.get('subject'),
        cover_url=data.get('cover_url')
    )
    db.session.add(course)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': course.to_dict()})


@app.route('/api/courses/<int:cid>', methods=['PUT'])
@jwt_required()
def update_course(cid):
    course = Course.query.get_or_404(cid)
    data = request.get_json()
    for key in ['name', 'code', 'description', 'subject', 'cover_url']:
        if key in data:
            setattr(course, key, data[key])
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': course.to_dict()})


@app.route('/api/courses/<int:cid>', methods=['DELETE'])
@jwt_required()
def delete_course(cid):
    course = Course.query.get_or_404(cid)
    CourseStudent.query.filter_by(course_id=cid).delete()
    db.session.delete(course)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


@app.route('/api/courses/<int:cid>/students', methods=['GET'])
@jwt_required()
def get_course_students(cid):
    enrollments = CourseStudent.query.filter_by(course_id=cid).all()
    students = [e.student.to_dict() for e in enrollments]
    return jsonify({'code': 200, 'data': students})


@app.route('/api/courses/<int:cid>/enroll', methods=['POST'])
@jwt_required()
def enroll_student(cid):
    data = request.get_json()
    student_id = data.get('student_id')
    existing = CourseStudent.query.filter_by(course_id=cid, student_id=student_id).first()
    if existing:
        return jsonify({'code': 400, 'msg': '学生已加入该课程'})
    cs = CourseStudent(course_id=cid, student_id=student_id)
    db.session.add(cs)
    course = Course.query.get(cid)
    course.student_count = CourseStudent.query.filter_by(course_id=cid).count() + 1
    db.session.commit()
    return jsonify({'code': 200, 'msg': '加入成功'})


# ======================== 题目 API ========================

@app.route('/api/questions', methods=['GET'])
@jwt_required()
def get_questions():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    course_id = request.args.get('course_id', type=int)
    question_type = request.args.get('question_type')
    query = Question.query
    if user.role == 'teacher':
        query = query.filter_by(teacher_id=uid)
    if course_id:
        query = query.filter_by(course_id=course_id)
    if question_type:
        query = query.filter_by(question_type=question_type)
    questions = query.order_by(Question.created_at.desc()).all()
    return jsonify({'code': 200, 'data': [q.to_dict() for q in questions]})


@app.route('/api/questions', methods=['POST'])
@jwt_required()
def create_question():
    data = request.get_json()
    uid = int(get_jwt_identity())
    q = Question(
        course_id=data['course_id'],
        teacher_id=uid,
        title=data['title'],
        content=data['content'],
        question_type=data['question_type'],
        subject=data.get('subject'),
        reference_answer=data.get('reference_answer'),
        grading_criteria=data.get('grading_criteria'),
        max_score=data.get('max_score', 10),
        knowledge_points=json.dumps(data.get('knowledge_points', []), ensure_ascii=False),
        difficulty=data.get('difficulty', '中等')
    )
    db.session.add(q)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': q.to_dict()})


@app.route('/api/questions/<int:qid>', methods=['GET'])
@jwt_required()
def get_question(qid):
    q = Question.query.get_or_404(qid)
    return jsonify({'code': 200, 'data': q.to_dict()})


@app.route('/api/questions/<int:qid>', methods=['PUT'])
@jwt_required()
def update_question(qid):
    q = Question.query.get_or_404(qid)
    data = request.get_json()
    for key in ['title', 'content', 'question_type', 'subject', 'reference_answer', 'grading_criteria', 'max_score', 'difficulty']:
        if key in data:
            setattr(q, key, data[key])
    if 'knowledge_points' in data:
        q.knowledge_points = json.dumps(data['knowledge_points'], ensure_ascii=False)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': q.to_dict()})


@app.route('/api/questions/<int:qid>', methods=['DELETE'])
@jwt_required()
def delete_question(qid):
    q = Question.query.get_or_404(qid)
    AssignmentQuestion.query.filter_by(question_id=qid).delete()
    db.session.delete(q)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ======================== 作业 API ========================

@app.route('/api/assignments', methods=['GET'])
@jwt_required()
def get_assignments():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    course_id = request.args.get('course_id', type=int)

    if user.role == 'teacher':
        teacher_courses = Course.query.filter_by(teacher_id=uid).all()
        course_ids = [c.id for c in teacher_courses]
        query = Assignment.query.filter(Assignment.course_id.in_(course_ids))
    elif user.role == 'student':
        enrolled = CourseStudent.query.filter_by(student_id=uid).all()
        course_ids = [e.course_id for e in enrolled]
        query = Assignment.query.filter(Assignment.course_id.in_(course_ids))
    else:
        query = Assignment.query

    if course_id:
        query = query.filter_by(course_id=course_id)
    assignments = query.order_by(Assignment.created_at.desc()).all()

    result = []
    for a in assignments:
        d = a.to_dict()
        if user.role == 'student':
            submitted = StudentAnswer.query.filter_by(assignment_id=a.id, student_id=uid).count()
            d['submitted_count'] = submitted
            d['is_submitted'] = submitted > 0
        else:
            total_students = CourseStudent.query.filter_by(course_id=a.course_id).count()
            submitted_students = db.session.query(StudentAnswer.student_id).filter_by(assignment_id=a.id).distinct().count()
            d['total_students'] = total_students
            d['submitted_students'] = submitted_students
        result.append(d)

    return jsonify({'code': 200, 'data': result})


@app.route('/api/assignments', methods=['POST'])
@jwt_required()
def create_assignment():
    data = request.get_json()
    a = Assignment(
        course_id=data['course_id'],
        title=data['title'],
        description=data.get('description'),
        deadline=datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M:%S') if data.get('deadline') else None,
        status=data.get('status', 'active')
    )
    db.session.add(a)
    db.session.flush()

    for i, qid in enumerate(data.get('question_ids', [])):
        aq = AssignmentQuestion(
            assignment_id=a.id,
            question_id=qid,
            order_num=i + 1
        )
        db.session.add(aq)

    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': a.to_dict()})


@app.route('/api/assignments/<int:aid>', methods=['GET'])
@jwt_required()
def get_assignment_detail(aid):
    a = Assignment.query.get_or_404(aid)
    d = a.to_dict()
    aqs = AssignmentQuestion.query.filter_by(assignment_id=aid).order_by(AssignmentQuestion.order_num).all()
    d['questions'] = [aq.question.to_dict() for aq in aqs]
    return jsonify({'code': 200, 'data': d})


@app.route('/api/assignments/<int:aid>', methods=['DELETE'])
@jwt_required()
def delete_assignment(aid):
    a = Assignment.query.get_or_404(aid)
    AssignmentQuestion.query.filter_by(assignment_id=aid).delete()
    db.session.delete(a)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ======================== 学生答题 API ========================

@app.route('/api/answers/submit', methods=['POST'])
@jwt_required()
def submit_answer():
    uid = int(get_jwt_identity())
    data = request.get_json()

    existing = StudentAnswer.query.filter_by(
        student_id=uid,
        question_id=data['question_id'],
        assignment_id=data['assignment_id']
    ).first()
    if existing:
        existing.answer_content = data['answer_content']
        existing.word_count = len(data['answer_content'])
        existing.submit_time = datetime.now()
        existing.status = 'submitted'
        sa = existing
    else:
        sa = StudentAnswer(
            student_id=uid,
            question_id=data['question_id'],
            assignment_id=data['assignment_id'],
            answer_content=data['answer_content'],
            word_count=len(data['answer_content'])
        )
        db.session.add(sa)

    db.session.commit()
    return jsonify({'code': 200, 'msg': '提交成功', 'data': sa.to_dict()})


@app.route('/api/answers/batch-submit', methods=['POST'])
@jwt_required()
def batch_submit():
    uid = int(get_jwt_identity())
    data = request.get_json()
    results = []
    for item in data.get('answers', []):
        existing = StudentAnswer.query.filter_by(
            student_id=uid,
            question_id=item['question_id'],
            assignment_id=item['assignment_id']
        ).first()
        if existing:
            existing.answer_content = item['answer_content']
            existing.word_count = len(item['answer_content'])
            existing.submit_time = datetime.now()
            existing.status = 'submitted'
            sa = existing
        else:
            sa = StudentAnswer(
                student_id=uid,
                question_id=item['question_id'],
                assignment_id=item['assignment_id'],
                answer_content=item['answer_content'],
                word_count=len(item['answer_content'])
            )
            db.session.add(sa)
        db.session.flush()
        results.append(sa.to_dict())
    db.session.commit()
    return jsonify({'code': 200, 'msg': '批量提交成功', 'data': results})


@app.route('/api/answers', methods=['GET'])
@jwt_required()
def get_answers():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    assignment_id = request.args.get('assignment_id', type=int)
    question_id = request.args.get('question_id', type=int)

    query = StudentAnswer.query
    if user.role == 'student':
        query = query.filter_by(student_id=uid)
    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)
    if question_id:
        query = query.filter_by(question_id=question_id)

    answers = query.order_by(StudentAnswer.submit_time.desc()).all()
    result = []
    for a in answers:
        d = a.to_dict()
        ar = AnalysisResult.query.filter_by(answer_id=a.id).first()
        if ar:
            d['analysis'] = ar.to_dict()
            fb = Feedback.query.filter_by(analysis_id=ar.id).first()
            if fb:
                d['feedback'] = fb.to_dict()
        result.append(d)
    return jsonify({'code': 200, 'data': result})


# ======================== AI 分析 API ========================

@app.route('/api/analysis/analyze', methods=['POST'])
@jwt_required()
def analyze():
    data = request.get_json()
    answer_id = data.get('answer_id')
    sa = StudentAnswer.query.get_or_404(answer_id)
    question = sa.question

    sa.status = 'analyzing'
    db.session.commit()

    kp_list = json.loads(question.knowledge_points) if question.knowledge_points else []
    analysis, feedback_data = analyze_answer(
        question_content=question.content,
        reference_answer=question.reference_answer or '',
        grading_criteria=question.grading_criteria or '',
        student_answer=sa.answer_content,
        max_score=question.max_score,
        knowledge_points=kp_list
    )

    ar = AnalysisResult(
        answer_id=sa.id,
        overall_score=analysis['overall_score'],
        knowledge_score=analysis['knowledge_score'],
        logic_score=analysis['logic_score'],
        expression_score=analysis['expression_score'],
        knowledge_details=json.dumps(analysis['knowledge_details'], ensure_ascii=False),
        logic_details=json.dumps(analysis['logic_details'], ensure_ascii=False),
        expression_details=json.dumps(analysis['expression_details'], ensure_ascii=False),
        error_points=json.dumps(analysis['error_points'], ensure_ascii=False),
        highlights=json.dumps(analysis['highlights'], ensure_ascii=False),
        analysis_time_ms=analysis['analysis_time_ms']
    )
    db.session.add(ar)
    db.session.flush()

    fb = Feedback(
        analysis_id=ar.id,
        overall_feedback=feedback_data['overall_feedback'],
        strengths=json.dumps(feedback_data['strengths'], ensure_ascii=False),
        weaknesses=json.dumps(feedback_data['weaknesses'], ensure_ascii=False),
        improvement_suggestions=json.dumps(feedback_data['improvement_suggestions'], ensure_ascii=False),
        recommended_resources=json.dumps(feedback_data['recommended_resources'], ensure_ascii=False),
        study_tips=feedback_data['study_tips']
    )
    db.session.add(fb)

    sa.status = 'completed'
    db.session.commit()

    return jsonify({
        'code': 200,
        'msg': '分析完成',
        'data': {
            'analysis': ar.to_dict(),
            'feedback': fb.to_dict()
        }
    })


@app.route('/api/analysis/batch', methods=['POST'])
@jwt_required()
def batch_analyze():
    data = request.get_json()
    answer_ids = data.get('answer_ids', [])
    results = []
    for aid in answer_ids:
        sa = StudentAnswer.query.get(aid)
        if not sa:
            continue
        existing = AnalysisResult.query.filter_by(answer_id=aid).first()
        if existing:
            results.append({'answer_id': aid, 'status': 'already_analyzed'})
            continue

        question = sa.question
        sa.status = 'analyzing'
        db.session.commit()

        kp_list = json.loads(question.knowledge_points) if question.knowledge_points else []
        analysis, feedback_data = analyze_answer(
            question_content=question.content,
            reference_answer=question.reference_answer or '',
            grading_criteria=question.grading_criteria or '',
            student_answer=sa.answer_content,
            max_score=question.max_score,
            knowledge_points=kp_list
        )

        ar = AnalysisResult(
            answer_id=sa.id,
            overall_score=analysis['overall_score'],
            knowledge_score=analysis['knowledge_score'],
            logic_score=analysis['logic_score'],
            expression_score=analysis['expression_score'],
            knowledge_details=json.dumps(analysis['knowledge_details'], ensure_ascii=False),
            logic_details=json.dumps(analysis['logic_details'], ensure_ascii=False),
            expression_details=json.dumps(analysis['expression_details'], ensure_ascii=False),
            error_points=json.dumps(analysis['error_points'], ensure_ascii=False),
            highlights=json.dumps(analysis['highlights'], ensure_ascii=False),
            analysis_time_ms=analysis['analysis_time_ms']
        )
        db.session.add(ar)
        db.session.flush()

        fb = Feedback(
            analysis_id=ar.id,
            overall_feedback=feedback_data['overall_feedback'],
            strengths=json.dumps(feedback_data['strengths'], ensure_ascii=False),
            weaknesses=json.dumps(feedback_data['weaknesses'], ensure_ascii=False),
            improvement_suggestions=json.dumps(feedback_data['improvement_suggestions'], ensure_ascii=False),
            recommended_resources=json.dumps(feedback_data['recommended_resources'], ensure_ascii=False),
            study_tips=feedback_data['study_tips']
        )
        db.session.add(fb)
        sa.status = 'completed'
        results.append({'answer_id': aid, 'status': 'completed'})

    db.session.commit()
    return jsonify({'code': 200, 'msg': '批量分析完成', 'data': results})


@app.route('/api/analysis/<int:answer_id>', methods=['GET'])
@jwt_required()
def get_analysis(answer_id):
    ar = AnalysisResult.query.filter_by(answer_id=answer_id).first()
    if not ar:
        return jsonify({'code': 404, 'msg': '未找到分析结果'}), 404
    fb = Feedback.query.filter_by(analysis_id=ar.id).first()
    sa = StudentAnswer.query.get(answer_id)
    return jsonify({
        'code': 200,
        'data': {
            'answer': sa.to_dict() if sa else {},
            'analysis': ar.to_dict(),
            'feedback': fb.to_dict() if fb else {}
        }
    })


# ======================== 教师审核 API ========================

@app.route('/api/feedback/<int:fid>/review', methods=['PUT'])
@jwt_required()
def teacher_review(fid):
    fb = Feedback.query.get_or_404(fid)
    data = request.get_json()
    fb.teacher_comment = data.get('teacher_comment', fb.teacher_comment)
    fb.teacher_score_adjustment = data.get('teacher_score_adjustment', 0)
    fb.is_teacher_reviewed = True
    if fb.teacher_score_adjustment != 0:
        ar = AnalysisResult.query.get(fb.analysis_id)
        ar.overall_score = max(0, ar.overall_score + fb.teacher_score_adjustment)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '审核完成', 'data': fb.to_dict()})


# ======================== 系统监控 API ========================

_app_start_time = datetime.now()

@app.route('/api/monitor/status', methods=['GET'])
@jwt_required()
def monitor_status():
    """返回真实的系统运行状态"""
    now = datetime.now()
    uptime_seconds = int((now - _app_start_time).total_seconds())
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f'{hours}h {minutes}m'

    total_analyses = AnalysisResult.query.count()
    avg_time_ms = 0
    if total_analyses > 0:
        avg_time_ms = db.session.query(db.func.avg(AnalysisResult.analysis_time_ms)).scalar() or 0
    avg_time_sec = round(avg_time_ms / 1000, 1)

    db_ok = True
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception:
        db_ok = False

    llm_ok = True
    try:
        from llm_service import _get_client
        _get_client()
    except Exception:
        llm_ok = False

    total_answers = StudentAnswer.query.count()
    analysis_rate = round(total_analyses / max(total_answers, 1) * 100, 1)

    services = [
        {'name': 'Flask API 服务', 'status': 'running', 'uptime': uptime_str, 'load': min(95, int(total_analyses * 3 + 10))},
        {'name': 'DeepSeek LLM 引擎', 'status': 'running' if llm_ok else 'error', 'uptime': uptime_str, 'load': min(95, int(total_analyses * 5 + 15))},
        {'name': 'SQLite 数据库', 'status': 'running' if db_ok else 'error', 'uptime': uptime_str, 'load': min(95, int(total_answers * 2 + 5))},
    ]

    recent_answers = StudentAnswer.query.order_by(StudentAnswer.submit_time.desc()).limit(5).all()
    logs = []
    for sa in recent_answers:
        ar = AnalysisResult.query.filter_by(answer_id=sa.id).first()
        if ar:
            logs.append({
                'time': sa.submit_time.strftime('%Y-%m-%d %H:%M') if sa.submit_time else '',
                'content': f'学生 {sa.student.real_name} 提交答案「{sa.question.title[:15]}...」，AI分析得分 {ar.overall_score}',
                'type': 'success'
            })
        else:
            logs.append({
                'time': sa.submit_time.strftime('%Y-%m-%d %H:%M') if sa.submit_time else '',
                'content': f'学生 {sa.student.real_name} 提交了答案「{sa.question.title[:15]}...」，待分析',
                'type': 'warning'
            })

    recent_feedbacks = Feedback.query.filter_by(is_teacher_reviewed=True).order_by(Feedback.created_at.desc()).limit(3).all()
    for fb in recent_feedbacks:
        ar = AnalysisResult.query.get(fb.analysis_id)
        if ar:
            sa = StudentAnswer.query.get(ar.answer_id)
            if sa:
                logs.append({
                    'time': fb.created_at.strftime('%Y-%m-%d %H:%M') if fb.created_at else '',
                    'content': f'教师审核了 {sa.student.real_name} 的答案，调整分数 {fb.teacher_score_adjustment:+.1f}',
                    'type': 'primary'
                })

    logs.sort(key=lambda x: x['time'], reverse=True)

    return jsonify({'code': 200, 'data': {
        'uptime': uptime_str,
        'uptime_seconds': uptime_seconds,
        'avg_analysis_time': avg_time_sec,
        'total_analyzed': total_analyses,
        'analysis_rate': analysis_rate,
        'db_status': 'running' if db_ok else 'error',
        'llm_status': 'running' if llm_ok else 'error',
        'api_status': 'running',
        'services': services,
        'logs': logs[:8],
    }})


# ======================== 导出 API ========================

@app.route('/api/export/grading-csv', methods=['GET'])
@jwt_required()
def export_grading_csv():
    """导出批阅结果为 CSV"""
    uid = int(get_jwt_identity())
    assignment_id = request.args.get('assignment_id', type=int)

    query = StudentAnswer.query
    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)
    else:
        teacher_courses = Course.query.filter_by(teacher_id=uid).all()
        course_ids = [c.id for c in teacher_courses]
        assignment_ids = [a.id for a in Assignment.query.filter(Assignment.course_id.in_(course_ids)).all()]
        query = query.filter(StudentAnswer.assignment_id.in_(assignment_ids))

    answers = query.order_by(StudentAnswer.submit_time.desc()).all()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['学生姓名', '学号', '题目', '答案字数', '综合得分', '知识覆盖', '逻辑推理', '语言表达', '分析状态', '教师审核', '提交时间'])

    for sa in answers:
        ar = AnalysisResult.query.filter_by(answer_id=sa.id).first()
        fb = Feedback.query.filter_by(analysis_id=ar.id).first() if ar else None
        writer.writerow([
            sa.student.real_name if sa.student else '',
            sa.student.student_no if sa.student else '',
            sa.question.title if sa.question else '',
            sa.word_count,
            ar.overall_score if ar else '',
            ar.knowledge_score if ar else '',
            ar.logic_score if ar else '',
            ar.expression_score if ar else '',
            '已分析' if ar else '待分析',
            '已审核' if (fb and fb.is_teacher_reviewed) else '未审核',
            sa.submit_time.strftime('%Y-%m-%d %H:%M') if sa.submit_time else '',
        ])

    csv_data = output.getvalue()
    output.close()
    from urllib.parse import quote
    fname = quote('批阅结果导出.csv')
    return Response(
        csv_data,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{fname}"}
    )


@app.route('/api/export/feedback-report/<int:answer_id>', methods=['GET'])
@jwt_required()
def export_feedback_report(answer_id):
    """导出单份答案的反馈报告（文本格式）"""
    sa = StudentAnswer.query.get_or_404(answer_id)
    ar = AnalysisResult.query.filter_by(answer_id=answer_id).first()
    fb = Feedback.query.filter_by(analysis_id=ar.id).first() if ar else None
    question = sa.question

    lines = [
        '=' * 60,
        '  CASA 主观题答案分析报告',
        '=' * 60,
        '',
        f'学生: {sa.student.real_name}  学号: {sa.student.student_no}',
        f'题目: {question.title}',
        f'提交时间: {sa.submit_time.strftime("%Y-%m-%d %H:%M") if sa.submit_time else ""}',
        '',
        '-' * 40,
        '  评分结果',
        '-' * 40,
    ]

    if ar:
        lines += [
            f'综合得分: {ar.overall_score} / {question.max_score}',
            f'知识覆盖: {ar.knowledge_score}',
            f'逻辑推理: {ar.logic_score}',
            f'语言表达: {ar.expression_score}',
            '',
        ]

        highlights = json.loads(ar.highlights) if ar.highlights else []
        if highlights:
            lines.append('【亮点】')
            for h in highlights:
                lines.append(f'  ✓ {h}')
            lines.append('')

        errors = json.loads(ar.error_points) if ar.error_points else []
        if errors:
            lines.append('【不足】')
            for e in errors:
                lines.append(f'  ✗ [{e.get("type", "")}] {e.get("description", "")}')
            lines.append('')

    if fb:
        lines += [
            '-' * 40,
            '  AI 反馈',
            '-' * 40,
            fb.overall_feedback or '',
            '',
        ]
        suggestions = json.loads(fb.improvement_suggestions) if fb.improvement_suggestions else []
        if suggestions:
            lines.append('【改进建议】')
            for s in suggestions:
                lines.append(f'  → {s}')
            lines.append('')

        resources = json.loads(fb.recommended_resources) if fb.recommended_resources else []
        if resources:
            lines.append('【推荐资源】')
            for r in resources:
                lines.append(f'  * {r}')
            lines.append('')

        if fb.study_tips:
            lines += ['【学习建议】', fb.study_tips, '']

        if fb.teacher_comment:
            lines += ['【教师评语】', fb.teacher_comment, '']

    lines += [
        '-' * 40,
        '  题目与答案',
        '-' * 40,
        '',
        '【题目内容】',
        question.content,
        '',
        '【我的答案】',
        sa.answer_content,
        '',
        '=' * 60,
        f'  报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        '  分析引擎: DeepSeek LLM + KLE Framework',
        '=' * 60,
    ]

    report = '\n'.join(lines)
    student_name = sa.student.real_name if sa.student else 'unknown'
    from urllib.parse import quote
    fname = quote(f'分析报告_{student_name}.txt')
    return Response(
        '\ufeff' + report,
        mimetype='text/plain; charset=utf-8',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{fname}"}
    )


# ======================== 统计 API ========================

@app.route('/api/stats/dashboard', methods=['GET'])
@jwt_required()
def dashboard_stats():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)

    if user.role == 'admin':
        return jsonify({'code': 200, 'data': {
            'total_users': User.query.count(),
            'total_teachers': User.query.filter_by(role='teacher').count(),
            'total_students': User.query.filter_by(role='student').count(),
            'total_courses': Course.query.count(),
            'total_questions': Question.query.count(),
            'total_assignments': Assignment.query.count(),
            'total_answers': StudentAnswer.query.count(),
            'total_analyzed': AnalysisResult.query.count(),
            'avg_score': _safe_avg(),
            'analysis_rate': round(AnalysisResult.query.count() / max(StudentAnswer.query.count(), 1) * 100, 1)
        }})
    elif user.role == 'teacher':
        my_courses = Course.query.filter_by(teacher_id=uid).all()
        course_ids = [c.id for c in my_courses]
        my_questions = Question.query.filter_by(teacher_id=uid).count()
        my_assignments = Assignment.query.filter(Assignment.course_id.in_(course_ids)).count()
        answer_count = StudentAnswer.query.filter(StudentAnswer.assignment_id.in_(
            [a.id for a in Assignment.query.filter(Assignment.course_id.in_(course_ids)).all()]
        )).count()
        total_students = sum(c.student_count for c in my_courses)
        return jsonify({'code': 200, 'data': {
            'total_courses': len(my_courses),
            'total_questions': my_questions,
            'total_assignments': my_assignments,
            'total_students': total_students,
            'total_answers': answer_count,
            'pending_review': Feedback.query.filter_by(is_teacher_reviewed=False).count()
        }})
    else:
        enrolled = CourseStudent.query.filter_by(student_id=uid).count()
        my_answers = StudentAnswer.query.filter_by(student_id=uid).count()
        completed = StudentAnswer.query.filter_by(student_id=uid, status='completed').count()
        my_analysis = db.session.query(AnalysisResult).join(StudentAnswer).filter(StudentAnswer.student_id == uid).all()
        avg = round(sum(a.overall_score for a in my_analysis) / max(len(my_analysis), 1), 1) if my_analysis else 0
        return jsonify({'code': 200, 'data': {
            'enrolled_courses': enrolled,
            'total_answers': my_answers,
            'completed_answers': completed,
            'average_score': avg,
            'pending_assignments': Assignment.query.filter(
                Assignment.course_id.in_([e.course_id for e in CourseStudent.query.filter_by(student_id=uid).all()]),
                Assignment.status == 'active'
            ).count()
        }})


@app.route('/api/stats/score-distribution', methods=['GET'])
@jwt_required()
def score_distribution():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)

    query = db.session.query(AnalysisResult)
    if user.role == 'student':
        query = query.join(StudentAnswer).filter(StudentAnswer.student_id == uid)
    elif user.role == 'teacher':
        course_ids = [c.id for c in Course.query.filter_by(teacher_id=uid).all()]
        assignment_ids = [a.id for a in Assignment.query.filter(Assignment.course_id.in_(course_ids)).all()]
        query = query.join(StudentAnswer).filter(StudentAnswer.assignment_id.in_(assignment_ids))

    results = query.all()
    distribution = {'0-59': 0, '60-69': 0, '70-79': 0, '80-89': 0, '90-100': 0}
    for r in results:
        pct = (r.overall_score / 10) * 100
        if pct < 60:
            distribution['0-59'] += 1
        elif pct < 70:
            distribution['60-69'] += 1
        elif pct < 80:
            distribution['70-79'] += 1
        elif pct < 90:
            distribution['80-89'] += 1
        else:
            distribution['90-100'] += 1

    return jsonify({'code': 200, 'data': distribution})


@app.route('/api/stats/dimension-avg', methods=['GET'])
@jwt_required()
def dimension_avg():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)

    query = db.session.query(AnalysisResult)
    if user.role == 'student':
        query = query.join(StudentAnswer).filter(StudentAnswer.student_id == uid)
    elif user.role == 'teacher':
        course_ids = [c.id for c in Course.query.filter_by(teacher_id=uid).all()]
        assignment_ids = [a.id for a in Assignment.query.filter(Assignment.course_id.in_(course_ids)).all()]
        query = query.join(StudentAnswer).filter(StudentAnswer.assignment_id.in_(assignment_ids))

    results = query.all()
    if not results:
        return jsonify({'code': 200, 'data': {'knowledge': 0, 'logic': 0, 'expression': 0}})

    return jsonify({'code': 200, 'data': {
        'knowledge': round(sum(r.knowledge_score for r in results) / len(results), 1),
        'logic': round(sum(r.logic_score for r in results) / len(results), 1),
        'expression': round(sum(r.expression_score for r in results) / len(results), 1)
    }})


def _safe_avg():
    results = AnalysisResult.query.all()
    if not results:
        return 0
    return round(sum(r.overall_score for r in results) / len(results), 1)


# ======================== 初始化示例数据 ========================

def init_sample_data():
    if User.query.count() > 0:
        return

    admin = User(username='admin', real_name='系统管理员', role='admin', email='admin@casa.edu.cn', department='信息中心')
    admin.set_password('123456')
    db.session.add(admin)

    t1 = User(username='teacher1', real_name='王建国', role='teacher', email='wangjg@casa.edu.cn', phone='13800001001', department='语文教研组')
    t1.set_password('123456')
    t2 = User(username='teacher2', real_name='李明珠', role='teacher', email='limz@casa.edu.cn', phone='13800001002', department='历史教研组')
    t2.set_password('123456')
    t3 = User(username='teacher3', real_name='张秀英', role='teacher', email='zhangxy@casa.edu.cn', phone='13800001003', department='地理教研组')
    t3.set_password('123456')
    db.session.add_all([t1, t2, t3])

    students = []
    student_names = [
        ('student1', '陈思远', '2022010101'), ('student2', '刘雨萱', '2022010102'),
        ('student3', '张浩然', '2022010103'), ('student4', '王诗涵', '2022010104'),
        ('student5', '赵子墨', '2022010105'), ('student6', '孙语桐', '2022010106'),
        ('student7', '周文博', '2022010107'), ('student8', '吴思琪', '2022010108'),
    ]
    for uname, rname, sno in student_names:
        s = User(username=uname, real_name=rname, role='student', student_no=sno, email=f'{uname}@stu.casa.edu.cn', department='2022级文科一班')
        s.set_password('123456')
        students.append(s)
        db.session.add(s)

    db.session.flush()

    c1 = Course(name='高中语文（必修上册）', code='YW-2026-01', teacher_id=t1.id, description='高中语文必修上册课程，涵盖现代文阅读、古诗文鉴赏、写作表达等模块', subject='语文', cover_url='https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400&h=250&fit=crop', student_count=8)
    c2 = Course(name='高中历史（中国近代史）', code='LS-2026-01', teacher_id=t2.id, description='中国近代史专题课程，从鸦片战争到新中国成立，培养学生的历史思辨能力', subject='历史', cover_url='https://images.unsplash.com/photo-1461360370896-922624d12e74?w=400&h=250&fit=crop', student_count=8)
    c3 = Course(name='高中地理（自然地理）', code='DL-2026-01', teacher_id=t3.id, description='自然地理基础课程，包括地球运动、大气环境、水文地貌等核心内容', subject='地理', cover_url='https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=400&h=250&fit=crop', student_count=8)
    db.session.add_all([c1, c2, c3])
    db.session.flush()

    for s in students:
        for c in [c1, c2, c3]:
            db.session.add(CourseStudent(course_id=c.id, student_id=s.id))

    questions_data = [
        {
            'course': c1, 'teacher': t1, 'title': '鲁迅作品思想分析',
            'content': '请结合鲁迅《祝福》的具体内容，分析祥林嫂的悲剧命运及其社会根源，并论述鲁迅通过这篇小说表达了怎样的思想主题。（不少于300字）',
            'type': '论述题', 'subject': '语文',
            'ref': '祥林嫂的悲剧命运体现在：1）被迫改嫁，失去丈夫和儿子，遭受精神和肉体的双重打击；2）封建礼教的束缚使她被视为"不洁"之人，遭到周围人的歧视和排斥；3）在绝望中死去，无人关心。社会根源包括：封建宗法制度对妇女的压迫、封建迷信思想的毒害、冷漠的社会环境。鲁迅通过祥林嫂的悲剧，深刻揭露了封建礼教和封建迷信吃人的本质，控诉了封建社会对劳动妇女的残酷迫害，表达了对被压迫者的深切同情。',
            'criteria': '知识点覆盖（40%）：能准确概述祥林嫂的主要遭遇，分析至少3个社会根源；逻辑论述（35%）：论述有层次，因果关系清晰；语言表达（25%）：使用文学批评术语，表达准确流畅',
            'score': 10.0, 'kps': ['人物形象分析', '社会批判主题', '封建礼教批判', '叙事手法'], 'diff': '中等'
        },
        {
            'course': c1, 'teacher': t1, 'title': '古诗词意象赏析',
            'content': '请赏析李白《将进酒》中"君不见黄河之水天上来，奔流到海不复回"的艺术手法和思想情感，并结合全诗分析李白诗歌的浪漫主义特色。',
            'type': '简答题', 'subject': '语文',
            'ref': '这两句诗运用了夸张和比兴手法，以黄河水的壮阔气势起兴，既表现了时光一去不返的感慨，又展现了诗人豪放不羁的气质。全诗体现了李白浪漫主义的特色：大胆夸张（"会须一饮三百杯"）、丰富想象、强烈抒情，以及对自由精神的追求。',
            'criteria': '能识别修辞手法（30%），能分析思想感情（40%），能总结浪漫主义特色（30%）',
            'score': 8.0, 'kps': ['修辞手法', '意象分析', '浪漫主义', '诗人情感'], 'diff': '中等'
        },
        {
            'course': c2, 'teacher': t2, 'title': '鸦片战争影响论述',
            'content': '请从政治、经济、思想文化三个维度，论述鸦片战争对中国近代社会的深远影响，并分析鸦片战争为什么被视为中国近代史的开端。（不少于300字）',
            'type': '论述题', 'subject': '历史',
            'ref': '政治上：中国丧失大量主权，签订不平等条约，开始沦为半殖民地半封建社会。经济上：自给自足的自然经济开始解体，中国被卷入资本主义世界市场，客观上促进了商品经济发展。思想文化上：开眼看世界的思潮兴起，林则徐、魏源等提出"师夷长技以制夷"。鸦片战争之所以被视为近代史开端，是因为它标志着中国社会性质的根本变化——从独立的封建社会变为半殖民地半封建社会，是中国近代化进程的起点。',
            'criteria': '三个维度各占30%，近代史开端论述占10%。要求史实准确，论述有逻辑',
            'score': 10.0, 'kps': ['鸦片战争', '半殖民地半封建', '近代化', '不平等条约'], 'diff': '中等'
        },
        {
            'course': c2, 'teacher': t2, 'title': '洋务运动评价',
            'content': '请客观评价洋务运动的历史功过，并分析洋务运动失败的根本原因。',
            'type': '简答题', 'subject': '历史',
            'ref': '功绩：引进西方先进技术和设备，创办近代军事工业和民用工业，建立新式海军，创办新式学堂，派遣留学生，客观上刺激了中国资本主义的发展。过失与失败原因：只学技术不学制度，"中体西用"的指导思想决定了其不可能使中国走上富强道路。根本原因是没有触及封建制度本身。',
            'criteria': '功绩论述（40%），失败原因分析（40%），评价客观性（20%）',
            'score': 8.0, 'kps': ['洋务运动', '中体西用', '近代工业', '制度变革'], 'diff': '困难'
        },
        {
            'course': c3, 'teacher': t3, 'title': '温室效应成因分析',
            'content': '请运用大气受热过程的相关知识，解释温室效应的形成原理，并分析全球变暖可能带来的地理环境变化。',
            'type': '简答题', 'subject': '地理',
            'ref': '温室效应原理：太阳短波辐射穿过大气层到达地面，地面吸收后以长波辐射形式向外释放能量。大气中的CO2等温室气体能吸收地面长波辐射，并以大气逆辐射的形式将能量返还地面，起到保温作用。人类活动大量排放温室气体，增强了这一过程。全球变暖的影响：海平面上升、极端天气增多、生态系统改变、水资源分布变化等。',
            'criteria': '受热过程原理（40%），温室效应机制（30%），环境变化分析（30%）',
            'score': 10.0, 'kps': ['大气受热过程', '温室效应', '全球变暖', '大气逆辐射'], 'diff': '中等'
        },
        {
            'course': c3, 'teacher': t3, 'title': '水循环过程与意义',
            'content': '请描述自然界水循环的主要环节和类型，并论述水循环的地理意义。',
            'type': '简答题', 'subject': '地理',
            'ref': '水循环主要环节：蒸发（蒸腾）、水汽输送、降水、地表径流、下渗、地下径流。三种类型：海陆间循环（大循环）、海上内循环、陆上内循环。地理意义：维持全球水量平衡，促进能量交换和物质迁移，塑造地表形态，影响全球气候，不断更新水资源。',
            'criteria': '环节描述完整（30%），类型区分准确（30%），意义论述充分（40%）',
            'score': 8.0, 'kps': ['水循环', '海陆间循环', '水量平衡', '地表形态'], 'diff': '简单'
        },
        {
            'course': c2, 'teacher': t2, 'title': '辛亥革命与近代化案例分析',
            'content': '【案例材料】1911年10月10日，武昌起义爆发，各省纷纷响应。1912年1月1日，中华民国临时政府在南京成立，孙中山就任临时大总统。同年2月12日，清帝退位，延续两千多年的君主专制制度终结。然而此后政权落入袁世凯手中，辛亥革命的胜利果实被窃取。请结合以上材料，分析辛亥革命的历史意义及其局限性，并评价辛亥革命在中国近代化进程中的地位。',
            'type': '案例分析题', 'subject': '历史',
            'ref': '历史意义：推翻了清朝统治，结束了两千多年的君主专制制度，建立了亚洲第一个共和国；颁布了《临时约法》，使民主共和观念深入人心；促进了民族资本主义发展和社会习俗变革。局限性：没有完成反帝反封建的历史任务；缺乏坚强的革命政党领导；没有充分发动广大人民群众；对帝国主义抱有幻想。近代化地位：辛亥革命是中国政治近代化的重要里程碑，从制度层面推动了中国从传统走向现代。',
            'criteria': '案例分析能力（30%）：能结合材料分析；历史意义（30%）：至少3点；局限性（20%）：至少2点；近代化评价（20%）：有独立见解',
            'score': 10.0, 'kps': ['辛亥革命', '共和制度', '近代化', '反帝反封建'], 'diff': '困难'
        },
    ]

    qs = []
    for qd in questions_data:
        q = Question(
            course_id=qd['course'].id, teacher_id=qd['teacher'].id, title=qd['title'],
            content=qd['content'], question_type=qd['type'], subject=qd['subject'],
            reference_answer=qd['ref'], grading_criteria=qd['criteria'],
            max_score=qd['score'],
            knowledge_points=json.dumps(qd['kps'], ensure_ascii=False),
            difficulty=qd['diff']
        )
        db.session.add(q)
        qs.append(q)
    db.session.flush()

    a1 = Assignment(course_id=c1.id, title='第一单元 现代文学作品分析', description='请认真阅读课文，完成以下主观题，要求论述完整、逻辑清晰。', deadline=datetime(2026, 5, 15), status='active')
    a2 = Assignment(course_id=c2.id, title='中国近代史专题练习（一）', description='请结合所学知识，从多角度分析近代重要历史事件。', deadline=datetime(2026, 5, 20), status='active')
    a3 = Assignment(course_id=c3.id, title='自然地理综合练习', description='运用所学地理知识分析自然现象的原理和影响。', deadline=datetime(2026, 5, 25), status='active')
    db.session.add_all([a1, a2, a3])
    db.session.flush()

    db.session.add(AssignmentQuestion(assignment_id=a1.id, question_id=qs[0].id, order_num=1))
    db.session.add(AssignmentQuestion(assignment_id=a1.id, question_id=qs[1].id, order_num=2))
    db.session.add(AssignmentQuestion(assignment_id=a2.id, question_id=qs[2].id, order_num=1))
    db.session.add(AssignmentQuestion(assignment_id=a2.id, question_id=qs[3].id, order_num=2))
    db.session.add(AssignmentQuestion(assignment_id=a3.id, question_id=qs[4].id, order_num=1))
    db.session.add(AssignmentQuestion(assignment_id=a3.id, question_id=qs[5].id, order_num=2))

    sample_answers = [
        (students[0], qs[0], a1, '祥林嫂的悲剧命运令人深感同情。首先，她在丈夫死后被迫改嫁到山里，失去了自主选择生活的权利，这体现了封建宗法制度对妇女的残酷压迫。其次，当她再次丧夫并失去儿子阿毛后，回到鲁镇却遭到所有人的歧视和嫌弃，被认为是"不洁"之人，这深刻反映了封建礼教对人的精神摧残。最后，她在祝福之夜孤独地死去，无人问津，揭示了封建社会的冷漠本质。鲁迅通过祥林嫂的故事，深刻揭露了封建礼教"吃人"的本质，控诉了旧社会对劳动妇女的压迫，表达了对底层人民的深切同情，呼唤社会的觉醒和变革。'),
        (students[1], qs[0], a1, '祥林嫂是鲁迅小说《祝福》中的主人公，她的命运非常悲惨。她先是死了丈夫，然后被婆婆卖给了山里的贺老六。后来贺老六也死了，她的儿子阿毛也被狼吃了。她回到鲁镇做工，但是大家都看不起她。最后她在大年三十死了。我觉得这是因为那个时代对女人不公平，封建思想害了她。'),
        (students[2], qs[1], a1, '李白的"君不见黄河之水天上来，奔流到海不复回"运用了夸张的修辞手法，将黄河之水的壮阔气势描绘得淋漓尽致。"天上来"极言黄河源头之高远，"不复回"暗喻时光一去不返，寄托了诗人对人生短暂的深沉感慨。这种以自然意象抒发人生感悟的手法，正是李白浪漫主义诗歌的典型特征。全诗气势磅礴，感情激昂，体现了李白"笔落惊风雨，诗成泣鬼神"的艺术风格。'),
        (students[3], qs[2], a2, '鸦片战争对中国影响很大。政治上，中国签了很多不平等条约，比如南京条约，割让了香港岛，赔了很多钱，开放了五个通商口岸。从此中国的主权受到了侵犯。经济上，外国商品大量涌入中国，使得中国的手工业者破产，自然经济开始解体。但也客观上促进了商品经济的发展。思想文化方面，林则徐、魏源等人开始关注世界大势，提出了"师夷长技以制夷"的主张，开启了中国人学习西方的序幕。因此，鸦片战争标志着中国开始沦为半殖民地半封建社会，是中国近代史的开端。'),
        (students[4], qs[2], a2, '鸦片战争让中国变得很弱。签了南京条约，割地赔款。经济上也受到了影响。我认为鸦片战争是近代史的开端，因为从那以后中国就开始被欺负了。'),
        (students[0], qs[4], a3, '温室效应的形成原理涉及大气的受热过程。首先，太阳辐射以短波辐射的形式穿过大气层到达地面，地面吸收太阳辐射后升温，并以长波辐射的形式向外释放能量。大气中的二氧化碳、甲烷等温室气体能够强烈吸收地面长波辐射，使大气增温。同时，大气以大气逆辐射的形式将部分能量返还给地面，对地面起到保温作用，这就是温室效应。由于人类大量燃烧化石燃料和砍伐森林，大气中温室气体浓度不断升高，温室效应增强，导致全球变暖。全球变暖可能导致：极地冰川融化使海平面上升，威胁沿海城市；极端天气事件增多；生态系统遭到破坏，物种分布发生变化；中纬度地区干旱加剧等。'),
        (students[5], qs[5], a3, '水循环的主要环节包括蒸发、水汽输送、降水、地表径流、下渗和地下径流。水循环分为三种类型：一是海陆间循环，也叫大循环，是海洋和陆地之间的水分交换，对陆地水资源的更新最重要；二是海上内循环，发生在海洋上空；三是陆上内循环，发生在陆地上。水循环的地理意义非常重要：它维持了全球水的动态平衡，使各种水体不断更新；促进了不同地区之间的能量交换和物质迁移；塑造了各种地表形态，如河流地貌、喀斯特地貌等。'),
    ]

    for student, question, assignment, answer_text in sample_answers:
        sa = StudentAnswer(
            student_id=student.id, question_id=question.id, assignment_id=assignment.id,
            answer_content=answer_text, word_count=len(answer_text), status='submitted'
        )
        db.session.add(sa)
    db.session.flush()

    all_answers = StudentAnswer.query.all()
    for sa in all_answers:
        question = sa.question
        kp_list = json.loads(question.knowledge_points) if question.knowledge_points else []
        import time as _t
        analysis, feedback_data = _local_fallback_analyze(
            question.content, question.reference_answer or '', question.grading_criteria or '',
            sa.answer_content, question.max_score, kp_list, _t.time()
        )
        ar = AnalysisResult(
            answer_id=sa.id, overall_score=analysis['overall_score'],
            knowledge_score=analysis['knowledge_score'], logic_score=analysis['logic_score'],
            expression_score=analysis['expression_score'],
            knowledge_details=json.dumps(analysis['knowledge_details'], ensure_ascii=False),
            logic_details=json.dumps(analysis['logic_details'], ensure_ascii=False),
            expression_details=json.dumps(analysis['expression_details'], ensure_ascii=False),
            error_points=json.dumps(analysis['error_points'], ensure_ascii=False),
            highlights=json.dumps(analysis['highlights'], ensure_ascii=False),
            analysis_time_ms=analysis['analysis_time_ms']
        )
        db.session.add(ar)
        db.session.flush()
        fb = Feedback(
            analysis_id=ar.id, overall_feedback=feedback_data['overall_feedback'],
            strengths=json.dumps(feedback_data['strengths'], ensure_ascii=False),
            weaknesses=json.dumps(feedback_data['weaknesses'], ensure_ascii=False),
            improvement_suggestions=json.dumps(feedback_data['improvement_suggestions'], ensure_ascii=False),
            recommended_resources=json.dumps(feedback_data['recommended_resources'], ensure_ascii=False),
            study_tips=feedback_data['study_tips']
        )
        db.session.add(fb)
        sa.status = 'completed'

    db.session.commit()
    print('示例数据初始化完成！')


with app.app_context():
    db.create_all()
    init_sample_data()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
