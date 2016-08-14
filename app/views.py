from flask import jsonify, request, send_from_directory
from sqlalchemy import desc
from sqlalchemy import and_

import app.models as models
import app.utils.view_utils as view_utils
from app import app
from app.utils import scrape_utils
from app.database import db
from app import cache
from flasgger.utils import swag_from


def make_key(*args, **kwargs):
    # """Make a key that includes GET parameters."""
    return str(hash(request.full_path))


@app.route('/')
def load_html():
    return send_from_directory('static', 'index.html')


@app.route('/static/script.js')
def load_js():
    return send_from_directory('static', 'script.js')


@app.route('/static/style.css')
def load_css():
    return send_from_directory('static', 'style.css')


@app.route('/update/courses')
def update_courses():
    return jsonify(data=scrape_utils.update_courses(), status='success')


@app.route('/update/schedules')
def update_sections():
    return jsonify(data=scrape_utils.update_schedules(), status='success')


@app.route('/update/trace')
def update_trace():
    cookie = request.args.get('cookie')
    return jsonify(data=scrape_utils.update_trace(cookie), status='success')


def create_response(results):
    response = []
    for r in results:
        response.append(r.to_json())
    return response


def check_response(response):
    if response:
        return jsonify(data=response, status='success')
    else:
        return jsonify(data='', status='success')


@app.route('/search-department', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/search_department.yaml')
def search_department():
    search, term_id, department_id, professor_name, attribute, level = get_query_params()

    if department_id:
        return jsonify(data='', status='success')

    response = view_utils.search_department_helper(
        search, term_id=term_id, professor_name=professor_name, department_id=department_id, attribute=attribute, level=level)

    return check_response(response)


@app.route('/search-level', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/search_level.yaml')
def search_level():
    search, term_id, department_id, professor_name, attribute, level = get_query_params()

    if level or search.lower() not in 'undergraduate':
        return jsonify(data='', status='success')

    response = view_utils.search_level_helper(
        search, term_id=term_id, professor_name=professor_name, department_id=department_id, attribute=attribute, level=level)

    return check_response(response)


@app.route('/search-attribute', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/search_attribute.yaml')
def search_attribute():
    search, term_id, department_id, professor_name, attribute, level = get_query_params()

    if attribute:
        return jsonify(data='', status='success')

    response = view_utils.search_attribute_helper(
        search, term_id=term_id, professor_name=professor_name, department_id=department_id, attribute=attribute, level=level)

    return check_response(response)


@app.route('/search-professor', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/search_professor.yaml')
def search_professor():
    search, term_id, department_id, professor_name, attribute, level = get_query_params()

    if professor_name:
        return jsonify(data='', status='success')

    response = view_utils.search_professor_helper(
        search, term_id=term_id, professor_name=professor_name, department_id=department_id, attribute=attribute, level=level)

    return check_response(response)


@app.route('/search-course', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/search_course.yaml')
def search_course():
    search, term_id, department_id, professor_name, attribute, level = get_query_params()

    response = view_utils.search_course_helper(
        search, term_id=term_id, professor_name=professor_name, department_id=department_id, attribute=attribute, level=level)

    return check_response(response)


@app.route('/professor', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_professors.yaml')
# @cache.memoize(timeout=0)
def api_professors():
    professors = models.Professor.query.order_by(
        models.Professor.professor_name).all()
    return jsonify(data=create_response(professors), status='success')


@app.route('/professor/<string:professor_name>', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_professor.yaml')
# @cache.memoize(timeout=0)
def api_professor(professor_name):
    professor = models.Professor.query.filter(models.Professor.professor_name == professor_name)\
                                .order_by(models.Professor.professor_name).all()
    return jsonify(data=create_response(professor), status='success')


@app.route('/department', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_departments.yaml')
# @cache.memoize(timeout=0)
def api_departments():
    departments = models.Department.query.order_by(
        models.Department.department_id).all()
    return jsonify(data=create_response(departments), status='success')


@app.route('/department/<string:department_id>', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_department.yaml')
# @cache.memoize(timeout=0)
def api_department(department_id):
    department = models.Department.query.filter(
        models.Department.department_id == department_id).all()
    return jsonify(data=create_response(department), status='success')


@app.route('/department/<string:department_id>/course', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_department_courses.yaml')
# @cache.memoize(timeout=0)
def api_department_courses(department_id):
    courses = models.Course.query.filter(
        models.Course.department_id == department_id).order_by(models.Course.course_number).all()
    return jsonify(data=create_response(courses), status='success')


@app.route('/department/<string:department_id>/course/<int:course_number>', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_department_course.yaml')
# @cache.memoize(timeout=0)
def api_department_course(department_id, course_number):
    course = models.Course.query.filter(
        models.Course.department_id == department_id, models.Course.course_number == course_number).all()
    return jsonify(data=create_response(course), status='success')


@app.route('/term', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_terms.yaml')
# @cache.memoize(timeout=0)
def api_terms():
    terms = models.Term.query.order_by(desc(models.Term.term_id)).all()
    return jsonify(data=create_response(terms), status='success')


@app.route('/term/<int:term_id>', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_term.yaml')
# @cache.memoize(timeout=0)
def api_term(term_id):
    term = models.Term.query.filter(models.Term.term_id == term_id).all()
    return jsonify(data=create_response(term), status='success')


@app.route('/term/<int:term_id>/department', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_term_departments.yaml')
# @cache.memoize(timeout=0)
def api_term_departments(term_id):
    departments = db.session.query(models.Department).\
        join(models.TermDepartment).filter(models.TermDepartment.term_id == term_id).\
        order_by(models.Department.department_id).all()
    return jsonify(data=create_response(departments), status='success')


@app.route('/term/<int:term_id>/department/<string:department_id>', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_term_department.yaml')
# @cache.memoize(timeout=0)
def api_term_department(term_id, department_id):
    department = db.session.query(models.Department).\
        join(models.TermDepartment).filter(and_(models.TermDepartment.term_id == term_id,
                                                models.Department.department_id == department_id)).all()
    return jsonify(data=create_response(department), status='success')


@app.route('/term/<int:term_id>/department/<string:department_id>/course', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_term_department_courses.yaml')
# @cache.memoize(timeout=0)
def api_term_department_courses(term_id, department_id):
    courses = db.session.query(models.Course).join(models.Section).filter(and_(models.Section.term_id == term_id,
                                                                               models.Course.department_id == department_id)).\
        order_by(models.Course.course_number).all()
    return jsonify(data=create_response(courses), status='success')


@app.route('/term/<int:term_id>/department/<string:department_id>/course/<int:course_number>', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_term_department_course.yaml')
# @cache.memoize(timeout=0)
def api_term_department_course(term_id, department_id, course_number):
    courses = db.session.query(models.Course).join(models.Section).filter(and_(models.Section.term_id == term_id,
                                                                               models.Course.course_number == course_number,
                                                                               models.Course.department_id == department_id)).all()
    return jsonify(data=create_response(courses), status='success')


@app.route('/term/<int:term_id>/department/<string:department_id>/course/<int:course_number>/section', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_term_department_course_sections.yaml')
# @cache.memoize(timeout=0)
def api_term_department_course_sections(term_id, department_id, course_number):
    sections = db.session.query(models.Section).filter(and_(models.Section.term_id == term_id,
                                                            models.Section.course_number == course_number,
                                                            models.Section.department_id == department_id)).\
        order_by(models.Section.crn).all()
    return jsonify(data=create_response(sections), status='success')


@app.route('/term/<int:term_id>/department/<string:department_id>/course/<int:course_number>/section/<int:crn>', methods=['GET'])
@cache.cached(timeout=0, key_prefix=make_key)
@swag_from('swagger/api_term_department_course_section.yaml')
# @cache.memoize(timeout=0)
def api_term_department_course_section(term_id, department_id, course_number, crn):
    sections = db.session.query(models.Section).filter(and_(models.Section.term_id == term_id,
                                                            models.Section.course_number == course_number,
                                                            models.Section.crn == crn,
                                                            models.Section.department_id == department_id)).all()
    return jsonify(data=create_response(sections), status='success')


def get_query_params():
    search = request.args.get('search')

    term_id = request.args.get('term')
    department_id = request.args.get('department')
    professor = request.args.get('professor')
    attribute = request.args.get('attribute')
    level = request.args.get('level')

    if not search:
        search = ""
    search = search.rstrip()

    return search, term_id, department_id, professor, attribute, level
