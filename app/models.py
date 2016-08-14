from sqlalchemy import Boolean, Column, Date, ForeignKey, ForeignKeyConstraint, Index, Integer, Text, Time
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql.base import ARRAY, TEXT
from sqlalchemy.dialects.postgresql.json import JSON
from flask import url_for
from flask_login import UserMixin

from app.database import db


class Model():
    def to_json(self, exclusions=[]):
        response = {}
        for key, val in self.__dict__.items():
            if key != '_sa_instance_state' and key not in exclusions:
                response[key] = str(val)
        return response


class CourseAttribute(db.Model, Model):
    """
    Represents the attributes of a course
    """
    __tablename__ = 'course_attributes'
    __table_args__ = (
        ForeignKeyConstraint(['department_id', 'course_number'], [u'courses.department_id', u'courses.course_number']),
        Index('course_attributes_index', 'attribute', 'is_searchable')
    )

    department_id = Column(Text, primary_key=True, nullable=False)
    course_number = Column(Integer, primary_key=True, nullable=False)
    attribute = Column(Text, primary_key=True, nullable=False)
    is_searchable = Column(Boolean)

    course = relationship(u'Course', backref=backref('attributes', lazy='dynamic'))

    def __repr__(self):
        return self.department_id + ' ' + str(self.course_number) + ' ' + self.attribute


class Course(db.Model, Model):
    """
    Represents a course
    """
    __tablename__ = 'courses'

    department_id = Column(ForeignKey(u'departments.department_id'), primary_key=True, nullable=False, index=True)
    course_number = Column(Integer, primary_key=True, nullable=False, index=True)
    course_name = Column(Text, index=True)
    course_description = Column(Text)
    course_url = Column(Text, unique=True)
    min_credit_hours = Column(Integer)
    max_credit_hours = Column(Integer)
    is_undergraduate = Column(Boolean)
    is_graduate = Column(Boolean)
    concurrent_prerequisites = Column(Boolean)
    full_prerequisite_description = Column(Text)
    prerequisites = Column(ARRAY(TEXT()))
    corequisites = Column(ARRAY(TEXT()))
    restrictions = Column(JSON)
    course_description_keywords = Column(Text)

    department = relationship(u'Department', backref=backref('courses', lazy='dynamic'))

    def __repr__(self):
        return self.department_id + ' ' + str(self.course_number) + ' - ' + self.course_name

    def to_json(self):
        response = super(Course, self).to_json(['min_credit_hours', 'max_credit_hours', 'course_description_keywords'])
        response['credit_hours'] = [self.min_credit_hours]
        if self.min_credit_hours != self.max_credit_hours:
            response['credit_hours'].append(self.max_credit_hours)

        response['attributes'] = [a.attribute for a in self.attributes]

        return response

    def to_link(self):
        return url_for('api_department_course', department_id=self.department_id, course_number=self.course_number)

    def to_section_link(self, term_id):
        return url_for('api_term_department_course', term_id=term_id, department_id=self.department_id, course_number=self.course_number)


class Department(db.Model, Model):
    """
    Represents a department with its id and name
    """
    __tablename__ = 'departments'
    __table_args__ = (
        Index('departments_index', 'department_id', 'department_name'),
    )

    department_id = Column(Text, primary_key=True)
    department_name = Column(Text)

    def __repr__(self):
        return self.department_id + ' ' + self.department_name

    def to_link(self):
        return url_for('api_department', department_id=self.department_id)


class Professor(db.Model, Model):
    """
    Represents a professor and his/her rating with a general summarized score and a detailed score
    """
    __tablename__ = 'professors'

    professor_name = Column(Text, primary_key=True, index=True)
    general_score = Column(Integer)
    all_scores = Column(JSON)

    def __repr__(self):
        return self.professor_name + ' ' + str(self.general_score) + ' ' + self.all_scores

    def to_link(self):
        return url_for('api_professor', professor_name=self.professor_name)


class SectionTime(db.Model, Model):
    """
    Represents the times of a section of a class.
    """
    __tablename__ = 'section_times'
    __table_args__ = (
        ForeignKeyConstraint(['crn', 'term_id'], [u'sections.crn', u'sections.term_id'], ondelete=u'CASCADE', onupdate=u'CASCADE'),
        Index('fki_section_times_fkey', 'crn', 'term_id')
    )

    crn = Column(Integer, primary_key=True, nullable=False)
    start_date = Column(Date, primary_key=True, nullable=False)
    end_date = Column(Date, primary_key=True, nullable=False)
    start_time = Column(Time, primary_key=True, nullable=False)
    end_time = Column(Time, primary_key=True, nullable=False)
    term_id = Column(Integer, primary_key=True, nullable=False)
    day_of_week = Column(Text, primary_key=True, nullable=False)

    section = relationship(u'Section', backref=backref('section_times', lazy='dynamic'))

    def __repr__(self):
        return (str(self.term_id) + ' ' + str(self.crn) + '\n' +
                'Start date: ' + str(self.start_date) + ' End date: ' + str(self.end_date) + '\n' +
                'Start time: ' + str(self.start_time) + ' End time: ' + str(self.end_time))


class Section(db.Model, Model):
    """
    Represents a section of a class with the associated fields such as:
    crn, location, section_id, professor, seats_left, and others
    """
    __tablename__ = 'sections'
    __table_args__ = (
        ForeignKeyConstraint(['department_id', 'course_number'], ['courses.department_id', 'courses.course_number']),
        Index('fki_courses_fkey', 'department_id', 'course_number'),
        Index('fki_sections_fkey', 'department_id', 'course_number')
    )

    department_id = Column(Text, index=True)
    course_number = Column(Integer)
    crn = Column(Integer, primary_key=True, nullable=False)
    section_id = Column(Text)
    location = Column(Text)
    min_credit_hours = Column(Integer)
    max_credit_hours = Column(Integer)
    section_type = Column(Text)
    term_id = Column(Integer, primary_key=True, nullable=False, index=True)
    capacity = Column(Integer)
    seats_taken = Column(Integer)
    seats_left = Column(Integer)
    room_size = Column(Integer)
    waitlist = Column(Integer)
    professor_name = Column(ForeignKey('professors.professor_name'), index=True)
    course_name = Column(Text)
    secondary_professor_names = Column(ARRAY(TEXT()))

    course = relationship('Course', backref=backref('sections', lazy='dynamic'))
    professor = relationship('Professor', backref=backref('sections', lazy='dynamic'))

    def __repr__(self):
        return (str(self.term_id) + ' ' + self.department_id + ' ' + str(self.course_number) + '\n' +
                str(self.crn) + ' ' + self.section_id + ' ' + self.professor_name)

    def to_json(self):
        response = super(Section, self).to_json(['min_credit_hours', 'max_credit_hours'])
        response['credit_hours'] = [self.min_credit_hours]
        if self.min_credit_hours != self.max_credit_hours:
            response['credit_hours'].append(self.max_credit_hours)
        response['times'] = [a.to_json(['term_id', 'crn']) for a in self.section_times]
        return response

    def to_link(self):
        return url_for('api_term_department_course_section', term_id=self.term_id, department_id=self.department_id, course_number=self.course_number, crn=self.crn)


class Term(db.Model, Model):
    """
    Represents a term using its name and id
    """
    __tablename__ = 'terms'

    term_id = Column(Integer, primary_key=True)
    term_name = Column(Text)

    def __repr__(self):
        return str(self.term_id) + ' ' + self.term_name

    def to_link(self):
        return url_for('api_term', term_id=self.term_id)


class TermDepartment(db.Model, Model):
    __tablename__ = 'term_departments'

    department_id = Column(ForeignKey('departments.department_id'), primary_key=True, nullable=False)
    term_id = Column(ForeignKey('terms.term_id'), primary_key=True, nullable=False)

    department = relationship('Department')
    term = relationship('Term')


class TraceSurveyQuestionKey(db.Model, Model):
    __tablename__ = 'trace_survey_question_key'

    key_id = Column(Integer, primary_key=True)
    trace_survey_question = Column(Text, unique=True)

    def __repr__(self):
        return str(self.key_id) + ' ' + self.trace_survey_question


class TraceSurvey(db.Model, Model):
    """
    Represents a trace survey object for each trace survey
    """
    __tablename__ = 'trace_surveys'

    department_id = Column(Text, nullable=False)
    course_number = Column(Integer, nullable=False)
    trace_survey_url = Column(Text, primary_key=True)
    section_id = Column(Text, nullable=False)
    term_name = Column(Text, nullable=False)
    survey_result = Column(JSON(none_as_null=True))
    professor_name = Column(ForeignKey(u'professors.professor_name'), index=True)

    professor = relationship(u'Professor', backref=backref('trace_survey', lazy='dynamic'))

    def __repr__(self):
        return (str(self.term_name) + ' ' + self.department_id + ' ' + str(self.course_number) + ' ' + self.section_id + '\n' +
                self.professor_name + '\n' + str(self.survey_result))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)
