#!flask/bin/python
import unittest
import json
import os

os.environ['APP_SETTINGS'] = "config.TestingConfig"

from config import basedir

from app import app
from app.database import db
import app.models as models
from app.utils import scrape_utils


def clear_tables():
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


class TestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        app.config['TESTING'] = True
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.environ['APP_SETTINGS'] = "config.DevelopmentConfig"

    def test_process_term_page(self):
        with open(basedir + '/test_resources/term_page_results.json') as data_file:
            data = json.load(data_file)
            data_term_ids = [int(a) for a in data.keys()]

            with open(basedir + '/test_resources/term_page.html') as input_file:
                scrape_utils.process_term_page(input_file.read())
            terms = models.Term.query.all()
            assert len(terms) == len(data)
            for term in terms:
                assert term.term_id in data_term_ids
                assert term.term_name == data[str(term.term_id)]

            assert models.Term.query.filter(
                models.Term.term_id == "201710").one().term_name == "Fall 2016 Semester"
            assert models.Term.query.filter(
                models.Term.term_name == "Summer 1 2015 Semester").one().term_id == 201540

            clear_tables()

    def test_process_department_page(self):
        with open(basedir + '/test_resources/department_page_results.json') as data_file:
            data = json.load(data_file)
            db.session.add(
                models.Term(term_name="Fall 2016 Semester", term_id=201710))
            db.session.commit()
            with open(basedir + '/test_resources/department_page.html') as input_file:
                scrape_utils.process_department_page(input_file.read(), 201710)

            departments = models.Department.query.all()

            assert len(departments) == len(data)
            for department in departments:
                assert department.department_id in data
                assert department.department_name == data[
                    department.department_id]

            assert models.Department.query.filter(
                models.Department.department_id == "CS").one().department_name == "Computer Science"
            assert models.Department.query.filter(
                models.Department.department_name == "Electrical and Computer Engineering").one().department_id == "EECE"

            clear_tables()

    def test_process_course_page(self):
        db.session.add(models.Department(
            department_id="EECE", department_name="Electrical and Computer Engineering"))
        db.session.commit()
        with open(basedir + '/test_resources/course_page.html') as input_file:
            scrape_utils.process_course_page(input_file.read(
            ), "https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=EECE&crse_numb_in=4644", "EECE", 4644)
        courses = db.session.query(models.Course).all()
        assert len(courses) == 1

        course = courses[0]
        assert course.course_description == 'Constitutes the lecture portion of an integrated lecture/lab. Covers circuit theory, signal processing, circuit building, and MATLAB programming. Introduces basic device and signal models and basic circuit laws used in the study of linear circuits. Analyzes resistive and complex impedance networks, including Thevenin equivalents. Uses the ideal operational amplifier model, focusing on differential amplifiers and active filter circuits. In the signal processing area, introduces the basic concepts of linearity and time-invariance for both continuous and discrete-time systems, as well as concepts associated with analog/digital conversion such as sampling and quantization. Demonstrates discrete-time linear filter design on acquired signals in the MATLAB environment.'
        assert course.full_prerequisite_description == 'Prereq. GE 1111, MATH 2341, and PHYS 1155 (the latter two may be taken concurrently); electrical engineering, computer engineering, and related combined majors only. Coreq. EECE 2151.'
        assert course.prerequisites == [
            'GE 1111', 'and', 'MATH 2341', 'and', 'PHYS 1155']
        assert course.corequisites == ['EECE 2151']
        assert course.course_number == 4644
        self.assertTrue(course.concurrent_prerequisites)
        assert course.restrictions == {'Programs': ['BSCMPE Computer Engineering', 'BSEE Electrical Engineering', 'BSCMPE Elect and Comp Engr',
                                                    'BSEE Electrical Engr/Physics', 'BSEE Elect and Comp Engr', 'BSCMPE Computer Engr/Comp. Sci', 'BSCMPE Comp Engineer/Physics'], 'Levels': ['Undergraduate']}
        self.assertFalse(course.is_graduate)
        self.assertTrue(course.is_undergraduate)
        assert course.department_id == 'EECE'
        assert course.min_credit_hours == 4
        assert course.max_credit_hours == 4
        assert course.course_url == 'https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=EECE&crse_numb_in=4644'
        assert course.course_name == 'Circuits and Signals: Biomedical Applications'
        assert course.course_description_keywords == 'constitutes lecture portion integrated lecture lab circuit theory signal processing circuit building matlab programming basic device signal models basic circuit laws used linear circuits analyzes resistive complex impedance networks thevenin equivalents uses ideal operational amplifier model differential amplifiers active filter circuits signal processing area basic concepts linearity time-invariance both continuous discrete-time systems concepts associated analog digital conversion sampling quantization demonstrates discrete-time linear filter design acquired signals matlab environment'

        clear_tables()

    def test_process_schedule_page(self):
        db.session.add(
            models.Department(department_id="ARAB", department_name="Arabic"))
        db.session.add(models.Course(department_id="ARAB", course_number=1101, course_name="Elementary Arabic 1",
                                     course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_display_courses?term_in=201710&one_subj=ARAB&sel_subj=&sel_crse_strt=1101&sel_crse_end=1101&sel_levl=&sel_schd=&sel_coll=&sel_divs=&sel_dept=&sel_attr="))
        db.session.add(models.Course(department_id="ARAB", course_number=1102, course_name="Elementary Arabic 2",
                                     course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_display_courses?term_in=201710&one_subj=ARAB&sel_subj=&sel_crse_strt=1102&sel_crse_end=1102&sel_levl=&sel_schd=&sel_coll=&sel_divs=&sel_dept=&sel_attr="))
        db.session.add(models.Course(department_id="ARAB", course_number=2101, course_name="Intermediate Arabic 1",
                                     course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_display_courses?term_in=201710&one_subj=ARAB&sel_subj=&sel_crse_strt=2101&sel_crse_end=2101&sel_levl=&sel_schd=&sel_coll=&sel_divs=&sel_dept=&sel_attr="))
        db.session.add(models.Course(department_id="ARAB", course_number=2102, course_name="Intermediate Arabic 2",
                                     course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_display_courses?term_in=201710&one_subj=ARAB&sel_subj=&sel_crse_strt=2102&sel_crse_end=2102&sel_levl=&sel_schd=&sel_coll=&sel_divs=&sel_dept=&sel_attr="))
        db.session.add(models.Course(department_id="ARAB", course_number=4800, course_name="ST: Decoding Classical Texts 2",
                                     course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_display_courses?term_in=201710&one_subj=ARAB&sel_subj=&sel_crse_strt=4800&sel_crse_end=4800&sel_levl=&sel_schd=&sel_coll=&sel_divs=&sel_dept=&sel_attr="))
        db.session.commit()
        with open(basedir + '/test_resources/section_page.html') as input_file:
            scrape_utils.process_schedule_page(
                input_file.read(), 201710, "ARAB")

        section = db.session.query(models.Section).filter(
            models.Section.crn == 10182).one()
        professor = db.session.query(models.Professor).filter(
            models.Professor.professor_name == "Muna Bruce").one()
        assert section.professor_name == professor.professor_name

        section = db.session.query(models.Section).filter(
            models.Section.crn == 10181).one()
        assert section.professor_name == professor.professor_name

        section = db.session.query(models.Section).filter(
            models.Section.crn == 10180).one()
        professor = db.session.query(models.Professor).filter(
            models.Professor.professor_name == "Shakir Mustafa").one()
        assert section.professor_name == professor.professor_name

        section = db.session.query(models.Section).filter(
            models.Section.crn == 11583).one()
        assert section.professor_name == professor.professor_name

        section = db.session.query(models.Section).filter(
            models.Section.crn == 11701).one()
        assert section.professor_name == professor.professor_name

        section = db.session.query(models.Section).filter(
            models.Section.crn == 16357).one()
        professor = db.session.query(models.Professor).filter(
            models.Professor.professor_name == "Mohammad A. Abderrazzaq").one()
        assert section.professor_name == professor.professor_name

        clear_tables()

    def test_proccess_trace_page(self):
        db.session.add(models.Professor(professor_name="Dana H. Brooks"))
        db.session.add(models.TraceSurvey(department_id="EECE", course_number="2150", term_name="Fall 2014", section_id="01",
                                          trace_survey_url="https://prod-web.neu.edu/wasapp/TRACE25/secure/detail.do?ciid=70004&sid=37", professor_name="Dana H. Brooks"))
        db.session.commit()
        with open(basedir + '/test_resources/trace_page.html') as input_file:
            scrape_utils.proccess_trace_page(input_file.read(
            ), "https://prod-web.neu.edu/wasapp/TRACE25/secure/detail.do?ciid=70004&sid=37", " ")
        scrape_utils.find_professor_summaries()

        trace = db.session.query(models.TraceSurvey).all()[0]
        professor = db.session.query(models.Professor).all()[0]

        assert json.loads(trace.survey_result) == {'13': {'4': 3, '3': 5, '0': 0, 'N/A': 3, '2': 1, '5': 4, '1': 0}, '9': {'4': 7, '3': 0, '0': 1, 'N/A': 0, '2': 0, '5': 8, '1': 0}, '17': {'4': 6, '3': 1, '0': 0, 'N/A': 0, '2': 0, '5': 9, '1': 0}, '2': {'4': 3, '3': 4, '0': 0, 'N/A': 1, '2': 3, '5': 3, '1': 2}, '5': {'4': 8, '3': 3, '0': 0, 'N/A': 0, '2': 0, '5': 5, '1': 0}, '19': {'4': 6, '3': 0, '0': 0, 'N/A': 0, '2': 0, '5': 10, '1': 0}, '7': {'4': 6, '3': 1, '0': 0, 'N/A': 0, '2': 1, '5': 8, '1': 0}, '18': {'4': 6, '3': 0, '0': 0, 'N/A': 0, '2': 0, '5': 10, '1': 0}, '11': {'4': 7, '3': 0, '0': 1, 'N/A': 0, '2': 0, '5': 8, '1': 0}, '12': {'4': 1, '3': 4, '0': 0, 'N/A': 4, '2': 3, '5': 4, '1': 0}, '22': {'4': 4, '3': 2, '0': 0, 'N/A': 0, '2': 0, '5': 10, '1': 0}, '24': {'4': 3, '3': 1, '0': 0, 'N/A': 0, '2': 0, '5': 12, '1': 0}, '4': {'4': 9, '3': 0, '0': 0, 'N/A': 0, '2': 1, '5': 6, '1': 0}, '3': {'4': 9, '3': 0, '0': 0, 'N/A': 0, '2': 0, '5': 7, '1': 0}, '10': {
            '4': 7, '3': 0, '0': 0, 'N/A': 0, '2': 0, '5': 9, '1': 0}, '0': {'Choose not to participate': 0, 'Will Participate': 16, 'No Response': 0}, '16': {'4': 5, '3': 0, '0': 0, 'N/A': 0, '2': 0, '5': 11, '1': 0}, '14': {'4': 6, '3': 0, '0': 0, 'N/A': 0, '2': 0, '5': 10, '1': 0}, '26': {'4': 3, '3': 0, '0': 0, 'N/A': 0, '2': 0, '5': 13, '1': 0}, '1': {'4': 4, '3': 6, '0': 0, 'N/A': 1, '2': 2, '5': 3, '1': 0}, '8': {'1-4': 0, '9-12': 8, '13-16': 4, '5-8': 3, 'No Response': 0, '17-29': 1}, '27': {'4': 8, '3': 0, '0': 0, '2': 0, '5': 8, '1': 0}, '15': {'4': 3, '3': 3, '0': 0, 'N/A': 0, '2': 0, '5': 10, '1': 0}, '21': {'4': 6, '3': 0, '0': 0, 'N/A': 0, '2': 1, '5': 9, '1': 0}, '20': {'4': 6, '3': 1, '0': 0, 'N/A': 0, '2': 0, '5': 9, '1': 0}, '25': {'4': 2, '3': 0, '0': 0, 'N/A': 0, '2': 0, '5': 14, '1': 0}, '23': {'4': 4, '3': 0, '0': 0, 'N/A': 0, '2': 0, '5': 12, '1': 0}, '6': {'4': 6, '3': 2, '0': 0, 'N/A': 0, '2': 0, '5': 8, '1': 0}}
        assert professor.general_score == 918
        assert json.loads(professor.all_scores) == {'15': {'multiplier': 2, 'total_score': 4.4375, 'count': 16, 'score': 71}, '22': {'multiplier': 6, 'total_score': 4.5, 'count': 16, 'score': 72}, '16': {'multiplier': 1, 'total_score': 4.6875, 'count': 16, 'score': 75}, '14': {'multiplier': 3, 'total_score': 4.625, 'count': 16, 'score': 74}, '26': {'multiplier': 3, 'total_score': 4.8125, 'count': 16, 'score': 77}, '20': {'multiplier': 1, 'total_score': 4.5, 'count': 16, 'score': 72}, '19': {
            'multiplier': 2, 'total_score': 4.625, 'count': 16, 'score': 74}, '24': {'multiplier': 2, 'total_score': 4.6875, 'count': 16, 'score': 75}, '21': {'multiplier': 3, 'total_score': 4.4375, 'count': 16, 'score': 71}, '27': {'multiplier': 6, 'total_score': 4.5, 'count': 16, 'score': 72}, '23': {'multiplier': 1, 'total_score': 4.75, 'count': 16, 'score': 76}, '18': {'multiplier': 2, 'total_score': 4.625, 'count': 16, 'score': 74}, '25': {'multiplier': 2, 'total_score': 4.875, 'count': 16, 'score': 78}}

        clear_tables()

    def test_api_professors(self):
        professor1 = models.Professor(
            professor_name="Chenyang E. Liu", general_score=995, all_scores={"foo": "bar", "fizz": "buzz"})
        professor2 = models.Professor(
            professor_name="Geoffrey X. Yu", general_score=642, all_scores={"hi": "hello", "bye": "buhbye"})
        professor3 = models.Professor(
            professor_name="Nick L. Flanders", general_score=942, all_scores={"a": "b", "c": "d", 1: 2, 3: 4})

        self.api_test_helper(
            link='/professor', to_test=[professor1, professor2, professor3])

    def test_api_departments(self):
        department1 = models.Department(
            department_id="CS", department_name="Computer Science")
        department2 = models.Department(
            department_id="EECE", department_name="Electrical and Computer Engineering")
        department3 = models.Department(
            department_id="MATH", department_name="Math")

        self.api_test_helper(
            link='/department', to_test=[department1, department2, department3])

    def test_api_courses(self):
        db.session.add(
            models.Department(department_id="CS", department_name="Computer Science"))

        course1 = models.Course(department_id="CS",
                                course_number=1100,
                                course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=CS&crse_numb_in=1100",
                                min_credit_hours=4,
                                max_credit_hours=4,
                                course_name="Computer Science and Its Applications",
                                full_prerequisite_description="Prereq. Not open to students in the College of Computer and Information Science or in the College of Engineering.",
                                is_graduate=False,
                                is_undergraduate=True,
                                restrictions={'Levels': ['Undergraduate'], 'Not Colleges': [
                                    'College of Engineering', 'Coll of Computer & Info Sci']},
                                prerequisites=[],
                                course_description="Introduces students to the field of computer science and the patterns of thinking that enable them to become intelligent users of software tools in a problem-solving setting. Examines several important software applications so that students may develop the skills necessary to use computers effectively in their own disciplines.",
                                corequisites=[])

        course2 = models.Course(department_id="CS",
                                course_number=2501,
                                course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=CS&crse_numb_in=2500",
                                min_credit_hours=4,
                                max_credit_hours=4,
                                course_name="Fundamentals of Computer Science 1",
                                full_prerequisite_description="Coreq. CS 2501.",
                                is_graduate=False,
                                is_undergraduate=True,
                                restrictions={"Levels": ["Undergraduate"]},
                                prerequisites=[],
                                course_description="Introduces the fundamental ideas of computing and the principles of programming. Discusses a systematic approach to word problems, including analytic reading, synthesis, goal setting, planning, plan execution, and testing. Presents several models of computing, starting from nothing more than expression evaluation in the spirit of high school algebra. No prior programming experience is assumed; therefore, suitable for freshman students, majors and nonmajors alike who wish to explore the intellectual ideas in the discipline.",
                                corequisites=["CS 2501"])

        course3 = models.Course(department_id="CS",
                                course_number=2800,
                                course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=CS&crse_numb_in=2800",
                                min_credit_hours=4,
                                max_credit_hours=4,
                                course_name="Logic and Computation",
                                full_prerequisite_description="Prereq. (a) CS 1800, MATH 1365, or MATH 2310 and (b) CS 2500. Coreq. CS 2801.",
                                is_graduate=False,
                                is_undergraduate=True,
                                restrictions={"Levels": ["Undergraduate"]},
                                prerequisites=[
                                    '(', 'CS 1800', 'or', 'MATH 1365', 'or', 'MATH 2310', ')', 'and', 'CS 2500'],
                                course_description="Introduces formal logic and its connections to computer and information science. Offers an opportunity to learn to translate statements about the behavior of computer programs into logical claims and to gain the ability to prove such assertions both by hand and using automated tools. Considers approaches to proving termination, correctness, and safety for programs. Discusses notations used in logic, propositional and first order logic, logical inference, mathematical induction, and structural induction. Introduces the use of logic for modeling the range of artifacts and phenomena that arise in computer and information science.",
                                corequisites=['CS 2801'])

        attribute1 = models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="ComputerandInfo Sci")
        attribute2 = models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="NU Core Science and Technology Level 1")
        attribute3 = models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="NUpath Formal and Quantitative Reasoning")
        attribute4 = models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="NUpath Natural and Designed World")

        self.api_test_helper(link='/department/CS/course', to_test=[
                             course1, course2, course3], to_add=[attribute1, attribute2, attribute3, attribute4])

    def test_api_terms(self):
        term1 = models.Term(term_name="Fall 2016 CPS Semester", term_id=201714)
        term2 = models.Term(term_name="Fall 2016 Law Semester", term_id=201712)
        term3 = models.Term(term_name="Fall 2016 Semester", term_id=201710)

        self.api_test_helper(link='/term', to_test=[term1, term2, term3])

    def test_api_term_departments(self):
        db.session.add(
            models.Term(term_name="Fall 2016 Semester", term_id=201710))
        db.session.add(
            models.Term(term_name="Fall 2016 CPS Semester", term_id=201714))
        term_department1 = models.TermDepartment(
            department_id="CS", term_id=201710)
        term_department2 = models.TermDepartment(
            department_id="EECE", term_id=201710)
        term_department3 = models.TermDepartment(
            department_id="MATH", term_id=201710)
        term_department4 = models.TermDepartment(
            department_id="DS", term_id=201714)

        department1 = models.Department(
            department_id="CS", department_name="Computer Science")
        department2 = models.Department(
            department_id="EECE", department_name="Electrical and Computer Engineering")
        department3 = models.Department(
            department_id="MATH", department_name="Math")
        department4 = models.Department(
            department_id="DS", department_name="Data Science")

        self.api_test_helper(link='/term/201710/department', to_test=[department1, department2, department3], to_add=[
                             department4, term_department1, term_department2, term_department3, term_department4])

    def test_api_term_department_courses(self):
        db.session.add(
            models.Term(term_name="Fall 2016 Semester", term_id=201710))
        db.session.add(
            models.Term(term_name="Fall 2016 CPS Semester", term_id=201714))
        db.session.add(
            models.Department(department_id="CS", department_name="Computer Science"))
        db.session.add(
            models.Professor(professor_name="N/A", general_score=995, all_scores={"foo": "bar", "fizz": "buzz"}))
        db.session.add(
            models.Professor(professor_name="Matthias Felleisen", general_score=642, all_scores={"hi": "hello", "bye": "buhbye"}))
        db.session.add(
            models.Professor(professor_name="David W. Sprague", general_score=642, all_scores={"hi": "hello", "bye": "buhbye"}))

        course1 = models.Course(department_id="CS",
                                course_number=1100,
                                course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=CS&crse_numb_in=1100",
                                min_credit_hours=4,
                                max_credit_hours=4,
                                course_name="Computer Science and Its Applications",
                                full_prerequisite_description="Prereq. Not open to students in the College of Computer and Information Science or in the College of Engineering.",
                                is_graduate=False,
                                is_undergraduate=True,
                                restrictions={'Levels': ['Undergraduate'], 'Not Colleges': [
                                    'College of Engineering', 'Coll of Computer & Info Sci']},
                                prerequisites=[],
                                course_description="Introduces students to the field of computer science and the patterns of thinking that enable them to become intelligent users of software tools in a problem-solving setting. Examines several important software applications so that students may develop the skills necessary to use computers effectively in their own disciplines.",
                                corequisites=[])

        course2 = models.Course(department_id="CS",
                                course_number=2501,
                                course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=CS&crse_numb_in=2500",
                                min_credit_hours=4,
                                max_credit_hours=4,
                                course_name="Fundamentals of Computer Science 1",
                                full_prerequisite_description="Coreq. CS 2501.",
                                is_graduate=False,
                                is_undergraduate=True,
                                restrictions={"Levels": ["Undergraduate"]},
                                prerequisites=[],
                                course_description="Introduces the fundamental ideas of computing and the principles of programming. Discusses a systematic approach to word problems, including analytic reading, synthesis, goal setting, planning, plan execution, and testing. Presents several models of computing, starting from nothing more than expression evaluation in the spirit of high school algebra. No prior programming experience is assumed; therefore, suitable for freshman students, majors and nonmajors alike who wish to explore the intellectual ideas in the discipline.",
                                corequisites=["CS 2501"])

        course3 = models.Course(department_id="CS",
                                course_number=2800,
                                course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=CS&crse_numb_in=2800",
                                min_credit_hours=4,
                                max_credit_hours=4,
                                course_name="Logic and Computation",
                                full_prerequisite_description="Prereq. (a) CS 1800, MATH 1365, or MATH 2310 and (b) CS 2500. Coreq. CS 2801.",
                                is_graduate=False,
                                is_undergraduate=True,
                                restrictions={"Levels": ["Undergraduate"]},
                                prerequisites=[
                                    '(', 'CS 1800', 'or', 'MATH 1365', 'or', 'MATH 2310', ')', 'and', 'CS 2500'],
                                course_description="Introduces formal logic and its connections to computer and information science. Offers an opportunity to learn to translate statements about the behavior of computer programs into logical claims and to gain the ability to prove such assertions both by hand and using automated tools. Considers approaches to proving termination, correctness, and safety for programs. Discusses notations used in logic, propositional and first order logic, logical inference, mathematical induction, and structural induction. Introduces the use of logic for modeling the range of artifacts and phenomena that arise in computer and information science.",
                                corequisites=['CS 2801'])

        attribute1 = models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="ComputerandInfo Sci")
        attribute2 = models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="NU Core Science and Technology Level 1")
        attribute3 = models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="NUpath Formal and Quantitative Reasoning")
        attribute4 = models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="NUpath Natural and Designed World")

        section1 = models.Section(capacity=19,
                                  course_name="Computer Science and Its Applications",
                                  course_number=1100,
                                  min_credit_hours=4,
                                  max_credit_hours=4,
                                  crn=11647,
                                  department_id="CS",
                                  location="West Village H 210",
                                  professor_name="N/A",
                                  room_size=55,
                                  seats_left=0,
                                  seats_taken=19,
                                  secondary_professor_names=[],
                                  section_id="01",
                                  section_type="Class",
                                  term_id=201710,
                                  waitlist=0)

        sectiontime1 = models.SectionTime(day_of_week="T",
                                          term_id=201710,
                                          crn=10421,
                                          end_date="2016-12-07",
                                          end_time="10:20:00",
                                          start_date="2016-09-07",
                                          start_time="09:15:00")

        section2 = models.Section(capacity=49,
                                  course_name="Lab for CS 2500",
                                  course_number=2501,
                                  min_credit_hours=1,
                                  max_credit_hours=1,
                                  crn=10421,
                                  department_id="CS",
                                  location="West Village H 210",
                                  professor_name="Matthias Felleisen",
                                  room_size=55,
                                  seats_left=3,
                                  seats_taken=46,
                                  secondary_professor_names=[],
                                  section_id="01",
                                  section_type="Class",
                                  term_id=201710,
                                  waitlist=0)

        sectiontime2 = models.SectionTime(day_of_week="T",
                                          term_id=201710,
                                          crn=10421,
                                          end_date="2016-12-07",
                                          end_time="11:30:00",
                                          start_date="2016-09-07",
                                          start_time="09:50:00")

        sectiontime3 = models.SectionTime(day_of_week="W",
                                          term_id=201710,
                                          crn=10421,
                                          end_date="2016-12-07",
                                          end_time="9:30:00",
                                          start_date="2016-09-07",
                                          start_time="06:50:00")

        section3 = models.Section(capacity=49,
                                  course_name="Logic and Computation",
                                  course_number=2800,
                                  min_credit_hours=4,
                                  max_credit_hours=4,
                                  crn=10279,
                                  department_id="CS",
                                  location="East Village 002",
                                  professor_name="David W. Sprague",
                                  room_size=59,
                                  seats_left=17,
                                  seats_taken=32,
                                  secondary_professor_names=[],
                                  section_id="01",
                                  section_type="Class",
                                  term_id=201714,
                                  waitlist=0)

        sectiontime4 = models.SectionTime(day_of_week="MWR",
                                          term_id=201710,
                                          crn=10421,
                                          end_date="2016-12-07",
                                          end_time="09:05:00",
                                          start_date="2016-09-07",
                                          start_time="08:00:00")

        self.api_test_helper(link='/term/201710/department/CS/course', to_test=[course1, course2], to_add=[
            course3, attribute1, attribute2, attribute3, attribute4, section1, section2, section3, sectiontime1, sectiontime2, sectiontime3, sectiontime4])

    def test_api_term_department_course_sections(self):
        db.session.add(
            models.Term(term_name="Fall 2016 Semester", term_id=201710))
        db.session.add(
            models.Term(term_name="Fall 2016 CPS Semester", term_id=201714))
        db.session.add(
            models.Department(department_id="CS", department_name="Computer Science"))
        db.session.add(
            models.Professor(professor_name="N/A", general_score=995, all_scores={"foo": "bar", "fizz": "buzz"}))
        db.session.add(
            models.Professor(professor_name="Matthias Felleisen", general_score=642, all_scores={"hi": "hello", "bye": "buhbye"}))
        db.session.add(
            models.Professor(professor_name="David W. Sprague", general_score=642, all_scores={"hi": "hello", "bye": "buhbye"}))

        db.session.add(models.Course(department_id="CS",
                                     course_number=1100,
                                     course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=CS&crse_numb_in=1100",
                                     min_credit_hours=4,
                                     max_credit_hours=4,
                                     course_name="Computer Science and Its Applications",
                                     full_prerequisite_description="Prereq. Not open to students in the College of Computer and Information Science or in the College of Engineering.",
                                     is_graduate=False,
                                     is_undergraduate=True,
                                     restrictions={'Levels': ['Undergraduate'], 'Not Colleges': [
                                         'College of Engineering', 'Coll of Computer & Info Sci']},
                                     prerequisites=[],
                                     course_description="Introduces students to the field of computer science and the patterns of thinking that enable them to become intelligent users of software tools in a problem-solving setting. Examines several important software applications so that students may develop the skills necessary to use computers effectively in their own disciplines.",
                                     corequisites=[]))

        db.session.add(models.Course(department_id="CS",
                                     course_number=2501,
                                     course_url="https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_course_detail?cat_term_in=201710&subj_code_in=CS&crse_numb_in=2500",
                                     min_credit_hours=4,
                                     max_credit_hours=4,
                                     course_name="Fundamentals of Computer Science 1",
                                     full_prerequisite_description="Coreq. CS 2501.",
                                     is_graduate=False,
                                     is_undergraduate=True,
                                     restrictions={
                                         "Levels": ["Undergraduate"]},
                                     prerequisites=[],
                                     course_description="Introduces the fundamental ideas of computing and the principles of programming. Discusses a systematic approach to word problems, including analytic reading, synthesis, goal setting, planning, plan execution, and testing. Presents several models of computing, starting from nothing more than expression evaluation in the spirit of high school algebra. No prior programming experience is assumed; therefore, suitable for freshman students, majors and nonmajors alike who wish to explore the intellectual ideas in the discipline.",
                                     corequisites=["CS 2501"]))

        db.session.add(models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="ComputerandInfo Sci"))
        db.session.add(models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="NU Core Science and Technology Level 1"))
        db.session.add(models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="NUpath Formal and Quantitative Reasoning"))
        db.session.add(models.CourseAttribute(
            department_id="CS", course_number=2501, attribute="NUpath Natural and Designed World"))

        section1 = models.Section(capacity=19,
                                  course_name="Computer Science and Its Applications",
                                  course_number=1100,
                                  min_credit_hours=4,
                                  max_credit_hours=4,
                                  crn=11647,
                                  department_id="CS",
                                  location="West Village H 210",
                                  professor_name="N/A",
                                  room_size=55,
                                  seats_left=0,
                                  seats_taken=19,
                                  secondary_professor_names=[],
                                  section_id="01",
                                  section_type="Class",
                                  term_id=201710,
                                  waitlist=0)

        sectiontime1 = models.SectionTime(day_of_week="T",
                                          term_id=201710,
                                          crn=10421,
                                          end_date="2016-12-07",
                                          end_time="10:20:00",
                                          start_date="2016-09-07",
                                          start_time="09:15:00")

        section2 = models.Section(capacity=49,
                                  course_name="Lab for CS 2500",
                                  course_number=2501,
                                  min_credit_hours=1,
                                  max_credit_hours=1,
                                  crn=10421,
                                  department_id="CS",
                                  location="West Village H 210",
                                  professor_name="Matthias Felleisen",
                                  room_size=55,
                                  seats_left=3,
                                  seats_taken=46,
                                  secondary_professor_names=[],
                                  section_id="01",
                                  section_type="Class",
                                  term_id=201710,
                                  waitlist=0)

        sectiontime2 = models.SectionTime(day_of_week="T",
                                          term_id=201710,
                                          crn=10421,
                                          end_date="2016-12-07",
                                          end_time="11:30:00",
                                          start_date="2016-09-07",
                                          start_time="09:50:00")

        sectiontime3 = models.SectionTime(day_of_week="W",
                                          term_id=201710,
                                          crn=10421,
                                          end_date="2016-12-07",
                                          end_time="9:30:00",
                                          start_date="2016-09-07",
                                          start_time="06:50:00")

        section3 = models.Section(capacity=49,
                                  course_name="Lab for CS 2500",
                                  course_number=2501,
                                  min_credit_hours=1,
                                  max_credit_hours=1,
                                  crn=10885,
                                  department_id="CS",
                                  location="West Village H 210",
                                  professor_name="Matthias Felleisen",
                                  room_size=55,
                                  seats_left=5,
                                  seats_taken=44,
                                  secondary_professor_names=[],
                                  section_id="01",
                                  section_type="Class",
                                  term_id=201710,
                                  waitlist=0)

        sectiontime4 = models.SectionTime(day_of_week="W",
                                          term_id=201710,
                                          crn=10421,
                                          end_date="2016-12-07",
                                          end_time="13:25:00",
                                          start_date="2016-09-07",
                                          start_time="11:45:00")

        self.api_test_helper(link='/term/201710/department/CS/course/2501/section', to_test=[section2, section3], to_add=[
            section1, sectiontime1, sectiontime2, sectiontime3, sectiontime4])

    def api_test_helper(self, link, **kwargs):
        to_test = kwargs['to_test']
        with app.test_request_context():
            for t in to_test:
                db.session.add(t)
                db.session.commit()
            if "to_add" in kwargs:
                for t in kwargs['to_add']:
                    db.session.add(t)
                    db.session.commit()
            response = json.loads(
                self.app.get(link).data.decode("utf-8"))['data']
            assert len(response) == len(to_test)
            for i in range(len(response)):
                assert response[i] == to_test[i].to_json()
            response = json.loads(
                self.app.get(to_test[0].to_link()).data.decode("utf-8"))['data']
            assert response[0] == to_test[0].to_json()

            clear_tables()


if __name__ == '__main__':
    unittest.main()
