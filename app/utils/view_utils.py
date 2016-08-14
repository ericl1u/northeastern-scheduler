from sqlalchemy import cast, String, func, or_, and_

import app.models as models
# from app import cache
# from app import celery


def xstr(s):
    return '' if s is None else str(s)


# @celery.task
def search_department_helper(search, term_id=None, professor_name=None, department_id=None, attribute=None, level=None):
    department_query = models.Department.query.join(models.Course).join(
        models.Section).join(models.Professor).join(models.CourseAttribute)

    department_query = build_query(department_query,
                                   term_id=term_id, professor_name=professor_name,
                                   department_id=department_id, attribute=attribute, level=level)

    department_full_match = department_query.filter(
        func.lower(models.Department.department_id) == func.lower(search)).one_or_none()

    departments = department_query.filter(or_(
        (models.Department.department_id.ilike("%" + xstr(search))),
        (models.Department.department_name.ilike("%" + xstr(search) + "%"))))\
        .order_by(models.Department.department_id).all()

    if department_full_match:
        departments.insert(
            0, departments.pop(departments.index(department_full_match)))
    return [a.to_json() for a in departments]


# @celery.task
def search_level_helper(search, term_id=None, professor_name=None, department_id=None, attribute=None, level=None):
    response = []

    course_level_query = models.Course.query.join(models.Section).join(
        models.Professor).join(models.CourseAttribute)

    course_level_query = build_query(course_level_query,
                                     term_id=term_id,
                                     professor_name=professor_name,
                                     department_id=department_id,
                                     attribute=attribute,
                                     level=level)
    if course_level_query.filter(models.Course.is_undergraduate == True).first():
        response.append('Undergraduate')
    if course_level_query.filter(models.Course.is_graduate == True).first() and search.lower() in 'graduate':
        response.append("Graduate")
    return response


# @celery.task
def search_attribute_helper(search, term_id=None, professor_name=None, department_id=None, attribute=None, level=None):
    course_attributes_query = models.CourseAttribute.query.join(
        models.Course).join(models.Section).join(models.Professor)

    course_attributes_query = build_query(course_attributes_query,
                                          term_id=term_id,
                                          professor_name=professor_name,
                                          department_id=department_id,
                                          attribute=attribute,
                                          level=level)

    course_attributes = course_attributes_query.filter(
        models.CourseAttribute.attribute.ilike("%" + xstr(search) + "%"),
        models.CourseAttribute.is_searchable) \
        .distinct(models.CourseAttribute.attribute) \
        .with_entities(models.CourseAttribute.attribute) \
        .order_by(models.CourseAttribute.attribute)

    return [a[0] for a in course_attributes]


# @celery.task
def search_course_helper(search, term_id=None, professor_name=None, department_id=None, attribute=None, level=None):
    response = []
    already_added = set()

    course_query = models.Course.query.join(models.CourseAttribute).join(
        models.Section).join(models.Professor)

    course_query = build_query(course_query,
                               term_id=term_id,
                               professor_name=professor_name,
                               department_id=department_id,
                               attribute=attribute,
                               level=level)

    if search and len(search) > 5 and len(search) < 10:
        if search[-4:].isdigit():
            course_number = int(search[-4:])
            department_id = search[:-4].replace('-', '').split(' ')[0].upper()
            course = course_query.filter(models.Course.department_id == department_id,
                                         models.Course.course_number == course_number).one_or_none()
            if course:
                response.append(course.to_json())
                already_added.add(repr(course))

    courses = course_query.filter(or_(models.Course.course_name.ilike("%" + xstr(search) + "%"),
                                      cast(models.Course.course_number, String).ilike("%" + xstr(search) + "%"))) \
        .group_by(models.Course.department_id, models.Course.course_number) \
        .limit(41).from_self() \
        .order_by(models.Course.department_id, models.Course.course_number).all()

    if len(courses) > 40 and not department_id and not attribute and not professor_name:
        return response

    for c in courses:
        if repr(c) not in already_added:
            response.append(c.to_json())
            already_added.add(repr(c))

    courses = course_query.filter(models.Course.course_description.ilike("%" + xstr(search) + "%")) \
        .group_by(models.Course.department_id, models.Course.course_number) \
        .limit(61 - len(response)).from_self() \
        .order_by(models.Course.department_id, models.Course.course_number).all()

    if len(courses) + len(response) > 60 and not department_id and not attribute and not professor_name:
        return response

    response += [c.to_json() for c in courses if repr(c) not in already_added]
    return response


# @celery.task
def search_professor_helper(search, term_id=None, professor_name=None, department_id=None, attribute=None, level=None):
    professor_query = models.Professor.query.join(models.Section).join(
        models.Course).join(models.CourseAttribute)
    professor_query = build_query(professor_query,
                                  term_id=term_id,
                                  professor_name=professor_name,
                                  department_id=department_id,
                                  attribute=attribute,
                                  level=level)

    professors = professor_query.filter(
        and_(models.Professor.professor_name.ilike("%" + xstr(search) + "%"), models.Professor.professor_name != "N/A")) \
        .group_by(models.Professor.professor_name) \
        .limit(61).from_self() \
        .order_by(models.Professor.professor_name).all()

    if len(professors) > 60 and not department_id:
        return None

    return [a.to_json() for a in professors]


def build_query(query, term_id=None, professor_name=None, department_id=None, attribute=None, level=None):
    is_undergraduate = False
    is_graduate = False
    if level:
        if level.lower() == "graduate":
            is_graduate = True
        if level.lower() == "undergraduate":
            is_undergraduate = True

    query_parameters = {}
    query_parameters[models.Section.term_id] = term_id
    query_parameters[models.Professor.professor_name] = professor_name
    query_parameters[models.Course.department_id] = department_id
    query_parameters[models.Course.is_undergraduate] = is_undergraduate
    query_parameters[models.Course.is_graduate] = is_graduate
    query_parameters[models.CourseAttribute.attribute] = attribute

    for param_type, param in query_parameters.items():
        if param:
            query = query.filter(param_type == param)

    return query
