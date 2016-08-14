import re
import multiprocessing
from itertools import repeat
import requests
from bs4 import BeautifulSoup
from sqlalchemy import and_
from unidecode import unidecode
from datetime import datetime
import string
import json

import app.models as models
from app.database import Session
from app import app


def update_courses(number_of_most_recent_terms=5):
    scrape_terms()
    scrape_departments()
    scrape_courses(number_of_most_recent_terms)


def update_schedules(number_of_most_recent_terms=5):
    scrape_schedule(number_of_most_recent_terms)


def update_trace(cookie):
    cookie = "__unam=75b9e72-153ee085296-5cfc8c29-59; fos.web.server=myneuweb05; fos.secure.web.server=myneuweb05; runId=-9031676450294553283; BANSSO=1B365211C7FE66AE8781E769606939A18FFB1F8C7397624D0415C1B9632FC4C3; LtpaToken2=x58PVSyfBRw4V+WALC/oEjYAlJgCIlb7F/zNuti/7x3yXx3h2Ew6NuunZxYueipU9aqE4bZj+K3IixC0o1X1RKDVW/ia+k5fn8NAYTaDNSiWIHGLDvkYSv17lTSSfjksEnwOe8NHUq/2pdzi/Z9dTtS54QXfDwEe5905W3X9fCYq09nlnU0aA4H0G6SnetlmPXI+Yi6XFjf2mUw3wjRCDvQQnjFo49iTNeP+bQ6PfBfPcyr8Zhe8iHJXoVo2Z67aTxp+dlUaxGduyI3tAc6XS0N4g0Q3RiTrnDc9ncPdADC92AId6NAskaHUdSwO2mku5oCVpsJiQ/pDU2Hk1Qn55c4V9P7adQjC6+lHVyBhEjLlZfyJ7Di7jT99XqtfJfxolbUe6Q8s6hnMJKYH0sifiUbk14emWRlgSprMx0NdE/Ai2M+rfGdQRpzPVeps9JV8eJ/PBJT1FVtsB2r7iloQ7QoVDNLjb1OulFKNUJy90MUeERejDH+oVuWP7zGtGEoaXKyUhdD88FeI3AZH7wSiRmMoym2+AEYV9qiVRkQ8VFwue12NL2Qob61/z+TBvrHN/A/QkzjAGoR6TgJn6O8s5c7Eks6wztEwJ4BX3Ojh6fvvA7jmpgVw3wdWsj8lkxUlKro42QzFS0yfijm0WEGphbWRPuHhmst+r0zdoBEX6UkBd7Khrr1zpe3Q3/DWNLSMs+8GQyHsNDCf1MPszPVOmQmrmEFKjcHR58WBn0M2WIpLeakod7mBydO1dEiRNcnpIiPG1W/HdfYMD2HQnh3uGQ==; LtpaToken=x/Tz8gjOKWxGrAx+pNeFH48T4BjeNHQCBcl2rRjuytnudjEvEK8/mh+ibvOHtzopT7bO71+7bngDbQOEuKgi3HWzh6QLgkXp5UecKvXwFzQwnQGPfWlCm9wCuLxFmfahwwDfaOWadV+Dddf5Ijq7Fc0/bMseMqaWl9clLmjUXkngtU1875/bxIEM5Rjw8kaZcw65m4fygFn4hLoDAQDPG6kYoRTiedCR+5MRpj+3d3BNeBUewgRyeGx9UkdMhttRa+K+PtY1lNsJj+yWknHI7gz8ysOKwR9Gq0GiUb7Od7m+oJjBqc480ajvuwuE4DbJCxWx7OOzlj2VDoYe0OpORg==; JSESSIONID=0000QNO8nb-07Y9IhsXPNzHfBW1:18h88ahqf; usid=OU6Ng7yzRLKuACZX3i8TUg__; usidsec=2m1NhUnJwENze+2RhDp7mg__"
    initiate_trace_question_key()
    scrape_trace_URLs(cookie)
    scrape_trace_URL_information_parallel(cookie)
    find_professor_summaries()


def scrape_terms():
    """
    Find all terms e.g. Fall 2016, Spring 2015 etc and their respective term ids
    """
    app.logger.info('Scraping terms')
    try:
        response = requests.post(
            "https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_dyn_ctlg")
    except Exception as e:
        app.logger.error('Error when accessing term page ' + '\n' + repr(e))
    try:
        process_term_page(response.text)
    except AttributeError as e:
        app.logger.error('Invalid page for scraping terms')

    app.logger.info('Terms scraped')


def process_term_page(webpage):
    """
    Scrapes the information of the term pages and extracts term information
    """
    try:
        webpage = BeautifulSoup(webpage, 'html5lib')
        session = Session()
        # Dictionary that maps term ID to term name e.g. 201710 : Fall 2016
        terms = {}
        for option in webpage.find("select", {"id": "term_input_id"}).find_all('option'):
            if option['value'].isdigit():
                # Clean term name
                term_name = option.text.replace(
                    '(View only)', '').replace('\n', '')
                terms[int(option['value'])] = term_name
                term = models.Term(
                    term_id=int(option['value']), term_name=term_name)
                app.logger.info(term)

                session.merge(term)
                try:
                    session.commit()
                except Exception as e:
                    session.rollback()
                    app.logger.error(
                        'Error when storing term ' + repr(term) + '\n' + repr(e))
        session.close()
    except AttributeError:
        raise
    except Exception as e:
        app.logger.error(
            'Error when parsing term page ' + webpage.prettify() + '\n' + repr(e))


def scrape_departments(term_ids=None):
    """
    Find all department ids in parallel

    Optional parameter term_ids where user can specify a specific term to process.
    If no term specified, process every term in the database
    """
    app.logger.info('Scraping departments in parallel')
    try:
        # If no term specified, process all terms
        if not term_ids:
            term_ids = models.Term.query.with_entities(
                models.Term.term_id).all()
            term_ids = [term_id[0] for term_id in term_ids]
    except Exception as e:
        app.logger.error('Error with retrieving terms ' + '\n' + repr(e))
    try:
        p = multiprocessing.Pool()
        p.map(find_department_page, term_ids)
        app.logger.info('Done scraping departments')
    except Exception as e:
        app.logger.error(
            'Error with parallel scraping of terms ' + str(term_ids) + '\n' + repr(e))


def find_department_page(term):
    """
    Finds the department page given a term id.
    """
    app.logger.info('Scraping ' + str(term) + ' for departments')
    try:
        session = requests.Session()
        session.mount(
            "https://", requests.adapters.HTTPAdapter(max_retries=10))
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {"STU_TERM_IN": term}
        response = session.post(
            "https://wl11gp.neu.edu/udcprod8/NEUCLSS.p_class_select", headers=headers, data=body)
    except Exception as e:
        app.logger.error(
            'Error when accessing department page for term: ' + str(term) + '\n' + repr(e))
    try:
        process_department_page(response.text, term)
    except AttributeError as e:
        app.logger.error(
            'Invalid page for scraping departments for term: ' + str(term) + '\n' + repr(e))


def process_department_page(webpage, term):
    """
    Parses webpage for all departments and store into database
    """
    try:
        webpage = BeautifulSoup(webpage, 'html5lib')
        # Dictionary that maps department key to department name e.g. CS ->
        # computer Science
        departments = {}
        options = webpage.find(
            "select", {"id": "subjct_id"}).find_all('option')
        for option in options:
            departments[option['value']] = option.text.replace('\n', '')
    except AttributeError:
        raise
    except Exception as e:
        app.logger.error(
            'Error when parsing department page ' + webpage.prettify() + '\n' + repr(e))
    try:
        departments.pop('%')
        session = Session()

        for key, val in departments.items():
            temp = val.split('-')
            temp = temp[-1]
            val = val[0:len(val) - 2 - len(temp)].strip()

            val = val.replace('&', 'and')
            val = re.sub(r'\bLvl\b', 'Level', val)
            val = re.sub(r'\bEngineer\b', 'Engineering', val)
            val = re.sub(r'\bCol\b', 'College', val)
            val = re.sub(r'\bComm\b', 'Communication', val)
            val = re.sub(r'\bEngineerng\b', 'Engineering', val)
            val = re.sub(r'\bComp\b', 'Computer', val)
            val = re.sub(r'\bSci\b', 'Science', val)
            val = re.sub(r'\bBus\b', 'Business', val)
            val = re.sub(r'\bLang,\b', 'Language', val)
            val = re.sub(r'\bMech\b', 'Mechanical', val)
            val = re.sub(
                r'\bPhys Therapy/Movemnt/Rehab\b', 'Physical Therapy Movement Rehab', val)
            val = re.sub(r'\bPub\b', 'Public', val)
            val = re.sub(r'\bSem\b', 'Seminar', val)
            val = re.sub(r'\bEd Psyc\b', 'Educational Psychology', val)
            val = re.sub(r'\bDev\b', 'Development', val)
            val = re.sub(r'\bTech\b', 'Technology', val)
            val = re.sub(r'\bEnviro Eng\b', 'Environmental Engineering', val)
            val = re.sub(r'\bMangmnt\b', 'Management', val)
            val = re.sub(r'\bCommunicatn\b', 'Communication', val)
            val = re.sub(r'\bEducatn\b', 'Education', val)
            val = re.sub(
                r'\bCoop/Exper Ed\b', 'Coop and Experiential Education', val)
            val = re.sub(r'\bArts/Med/Dsgn\b', 'Arts Media and Design', val)
            val = re.sub(r'\bEvolutn\b', 'Evolution', val)
            val = re.sub(r'\bBiol\b', 'Biology', val)
            val = re.sub(
                r'\bSoc Sci/Hum\b', 'Social Science and Humanities', val)
            val = re.sub(
                r'\bSoc Sc/Hum\b', 'Social Science and Humanities', val)
            val = re.sub(r'\bTechnol\b', 'Technology', val)
            val = re.sub(r'\bElectricl\b', 'Electrical', val)
            val = re.sub(r'\bMed Serv\b', 'Medical Services', val)
            val = re.sub(r'\bCooperative Ed\b', 'Cooperative Education', val)
            val = re.sub(r'\bEnvironmentl\b', 'Environmental', val)
            val = re.sub(r'\bScnd Lang\b', 'Second Language', val)
            val = re.sub(r'\bElec\b', 'Electrical', val)
            val = re.sub(r'\bEng\b', 'Engineering', val)
            val = re.sub(r'\bGenerl\b', 'General', val)
            val = re.sub(r'\bEnviron\b', 'Environmental', val)
            val = re.sub(
                r'\bCoop/Experiential\b', 'Coop and Experiential', val)
            val = re.sub(r'\bEnv\b', 'Environmental', val)
            val = re.sub(r'\bSys\b', 'Systems', val)
            val = re.sub(r'\bMgmt\b', 'Management', val)
            val = re.sub(r'\bInterdisc\b', 'Interdisciplinary', val)
            val = re.sub(r'\bInterdiscpln\b', 'Interdisciplinary', val)
            val = re.sub(r'\bInfo\b', 'Informational', val)
            val = re.sub(r'\bStdy\b', 'Study', val)
            val = re.sub(r'\bProg\b', 'Programs', val)
            val = re.sub(r'\bAm & Carib\b', 'American and Caribbean', val)
            val = re.sub(r'\bStu\b', 'Students', val)
            val = re.sub(r'\bMechanicl\b', 'Mechanical', val)
            val = re.sub(r'\bManagemnt\b', 'Management', val)
            val = re.sub(r'\bAdministratn\b', 'Administration', val)
            val = re.sub(r'\bProf\b', 'Professional', val)
            val = re.sub(r'\bDevlpmnt\b', 'Development', val)
            val = re.sub(r'\bProgs\b', 'Progress', val)
            val = re.sub(r'\bSpeech-Lang\b', 'Speech Language', val)
            val = re.sub(r'\bCommunic\b', 'Communication', val)
            val = re.sub(
                r'\bSoc Science/Hum\b', 'Social Science/Humanities', val)
            val = re.sub(r'\bTelecom\b', 'Telecommunication', val)
            val = val.replace(',', '')

            department = models.Department(
                department_id=key, department_name=val)
            session.merge(department)
            try:
                session.commit()
            except Exception as e:
                app.logger.error(
                    'Error when storing department ' + repr(department) + '\n' + repr(e))
                session.rollback()

        for department in departments.keys():
            term_department = models.TermDepartment(
                term_id=term, department_id=department)
            session.merge(term_department)
            try:
                session.commit()
            except Exception as e:
                app.logger.error(
                    'Error when updating terms with departments ' + repr(term) + '\n' + repr(e))
                session.rollback()
        session.close()

    except Exception as e:
        app.logger.error(
            'Error when parsing department page ' + webpage.prettify() + '\n' + repr(e))


def scrape_courses(number_of_most_recent_terms=1):
    """
    Scrapes informations for all courses given the number of  most recent terms to deal with.
    Default only deals with the single most recent term
    """

    app.logger.info(
        'Scraping course urls for ' + str(number_of_most_recent_terms) + ' terms')
    try:
        term_ids = models.Term.query.with_entities(models.Term.term_id).all()
        term_ids = [term_id[0] for term_id in term_ids]
        # Processes only the specified amount of terms
        term_ids.sort()
        if number_of_most_recent_terms < len(term_ids):
            number_of_most_recent_terms = number_of_most_recent_terms * -1
            term_ids = term_ids[number_of_most_recent_terms:]
    except Exception as e:
        app.logger.error(
            'Error retrieving terms when scraping courses ' + '\n' + repr(e))

    app.logger.info('Scraping terms ' + str(term_ids))
    try:
        p = multiprocessing.Pool()
        for term_id in sorted(term_ids, reverse=True):
            session = Session()
            try:
                department_ids = [a[0] for a in session.query(models.TermDepartment.department_id).filter(
                    models.TermDepartment.term_id == term_id).all()]
            except Exception as e:
                app.logger.error(
                    'Error retrieving departments when scraping courses ' + '\n' + repr(e))
            session.close()
            if department_ids:
                p.starmap(
                    find_course_urls_page, zip(department_ids, repeat(term_id)))

    except Exception as e:
        app.logger.error(
            'Error with parallel scraping of courses ' + '\n' + str(e))

    app.logger.info('Finished scraping course urls')


def find_course_urls_page(department_id, term_id):
    """
    Given a department_id and term_id, finds the course page that contains all of the
    course urls. Utilizes process_course_url_page to find those urls and extracts the
    information inside those course pages.
    """
    try:
        app.logger.info(
            "Finding course urls from " + department_id + "\t" + str(term_id))

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = ("term_in=" + str(term_id) +
                "&call_proc_in=bwckctlg.p_disp_dyn_ctlg"
                "&sel_subj=dummy&sel_levl=dummy"
                "&sel_schd=dummy&sel_coll=dummy"
                "&sel_divs=dummy&sel_dept=dummy"
                "&sel_attr=dummy&sel_subj=" + department_id +
                "&sel_crse_strt=&sel_crse_end="
                "&sel_title="
                "&sel_levl=%25"
                "&sel_schd=%25"
                "&sel_coll=%25"
                "&sel_divs=%25"
                "&sel_dept=%25"
                "&sel_from_cred="
                "&sel_to_cred="
                "&sel_attr=%25")

        # Find all courses associated with department
        session = requests.Session()
        session.mount(
            "https://", requests.adapters.HTTPAdapter(max_retries=10))
        response = session.post(
            "https://wl11gp.neu.edu/udcprod8/bwckctlg.p_display_courses", headers=headers, data=data)
    except Exception as e:
        app.logger.error('Error trying to access course url page for ' +
                         str(term_id) + ' ' + department_id + '\n' + repr(e))

    try:
        process_course_url_page(response.text, department_id)
    except AttributeError as e:
        app.logger.error('None existing class page\t' +
                         department_id + "\t" + str(term_id) + '\n' + repr(e))


def process_course_url_page(webpage, department_id):
    try:
        webpage = BeautifulSoup(webpage, 'html5lib').find(
            "table", {"class": "datadisplaytable"}).tbody.find_all("td", {"class": "nttitle"})
        if not webpage:
            raise AttributeError
    except AttributeError:
        raise
    except Exception as e:
        app.logger.error(
            'Error parsing webpage' + webpage.prettify() + repr(e))
    try:
        for element in webpage:
            # Follows link for each course to get better description
            for link in element:
                if link.has_attr('href'):
                    # Full course link
                    url = "https://wl11gp.neu.edu" + link['href']
                    course_number = int(url[-4:])
                    session = Session()
                    try:
                        course_url = session.query(models.Course).filter(
                            and_(models.Course.department_id == department_id, models.Course.course_number == course_number)).one().course_url
                    except:
                        course_url = None
                    session.close()
                    if not course_url or url > course_url:
                        app.logger.info(
                            "Examining course " + department_id + "\t" + str(course_number) + "\t" + url)
                        try:
                            session = requests.Session()
                            session.mount(
                                "https://", requests.adapters.HTTPAdapter(max_retries=10))
                            response = session.get(url=url)
                            try:
                                process_course_page(
                                    response.text, url, department_id, course_number)
                            except Exception as e:
                                app.logger.error(
                                    'Error when parsing course page: ' + url + '\n' + repr(e))
                        except Exception as e:
                            app.logger.error(
                                'Error when accessing course urls page: ' + url + '\n' + repr(e))
    except Exception as e:
        app.logger.error(
            'Error when parsing course urls page: ' + webpage.prettify() + '\n' + repr(e))


def process_course_page(webpage, url, department_id, course_number):
    # Try to find the name of the course, if it doesn't exist, the page doesn't exist
    # Sometimes the neu course page will link to courses that don't exist, then its necessary
    # to check older versions of the url to see if any of those urls are valid
    try:
        soup = BeautifulSoup(webpage, 'html5lib').find(
            "table", {"class": "datadisplaytable"}).tbody

        name = soup.find("td", {"class": "nttitle"}).text.split(
            '-', 1)[1].strip()

        app.logger.info(
            "Scraping " + department_id + '\t' + str(course_number))
        # The entire text of the course
        full_page_text = soup.find("td", {"class": "ntdefault"})
        # Prerequisites are stored in italics if there are prerequisites
        full_prerequisite_description = full_page_text.i.text.strip(
        ) if full_page_text.i else ""
        # Split text by bold fields
        full_page_text = full_page_text.prettify().split(
            "<span class=\"fieldlabeltext\">")
        # The first bold field split holds the course description and extra
        # information such as credit hours
        full_course_description = BeautifulSoup(
            full_page_text[0], 'html5lib').text.split("\n")
        # Eliminate spaces and new liness
        split_course_description = [
            s for s in full_course_description if len(s) > 1]
        # Course description is the first element in the split
        course_description = unidecode(split_course_description[0].strip())
        # Determine credit hours
        for description in split_course_description:
            if "Credit hour" in description or "Continuing Education" in description:
                credit_hours = re.findall(
                    "\d+\.\d+", description) if re.findall("\d+\.\d+", description) else ""
                # Courses could have more than 1 credit hour choice
                credit_hours = [float(i) for i in credit_hours]
                if len(credit_hours) > 0:
                    break

        level = ""
        schedule_type = ""
        course_attributes = ""
        restrictions = {}
        prerequisites = []
        corequisites = []
        all_prerequisites = []
        ordering = []

        for attribute in full_page_text:

            soup = BeautifulSoup(attribute, 'html5lib')
            attribute_text = soup.text
            description = attribute_text.split()[0]

            if "Levels" in description:

                level = attribute_text.replace(
                    "Levels:", "").strip().split(',')
                level = [s.strip() for s in level if len(s) > 1]
            elif "Schedule" in description:

                schedule_type = attribute_text.replace(
                    "Schedule Types:", "").split('\n')
                schedule_type = [s for s in schedule_type if len(s) > 1]
                schedule_type = schedule_type[0].strip()

            elif "Course" in description:

                course_attributes = attribute_text.replace(
                    "Course Attributes:", "").strip().split(',')
                course_attributes = [s.strip()
                                     for s in course_attributes if len(s) > 1]

            elif "Restrictions" in description:

                for a in attribute_text.replace("Restrictions:", "").strip().replace('May', 'Must').split('Must'):

                    restriction_type = None

                    if "Levels" in a:
                        restriction_type = "Levels"
                    elif "Colleges" in a:
                        restriction_type = "Colleges"
                    elif "Programs" in a:
                        restriction_type = "Programs"
                    elif "Classifications" in a:
                        restriction_type = "Classifications"
                    elif "Majors" in a:
                        restriction_type = "Majors"

                    if "not" in a:
                        restriction_type = "Not " + restriction_type

                    if restriction_type:
                        a = a.replace(restriction_type + ":", "").split("\n")
                        a = [s.strip()
                             for s in a if len(s) > 1 and 'one of the following' not in s]
                        restrictions[restriction_type] = a
            #Levels, Colleges, Programs, Classifications
            elif "Prerequisites" in description:

                ordering = attribute_text.replace(
                    "(", " ( ").replace(")", " ) ").split()
                ordering = [s for s in ordering if any(
                    [seq == s for seq in ["and", "or", "(", ")"]])]

                all_prerequisite_splits = attribute_text.replace(
                    "Prerequisites:", "").replace("and", "or").split("or")

                prereq_links = []
                for a in soup.find_all('a'):
                    prereq_links.append(a.text.strip())
                # Fixes empty prereqs
                prereq_links = [s for s in prereq_links if len(s.strip()) > 1]

                for prereq in all_prerequisite_splits:
                    input_text = None
                    for prereq_link in prereq_links:
                        if prereq_link in prereq:
                            input_text = prereq_link
                    if input_text is not None:
                        prerequisites.append(input_text)
                    else:
                        prerequisites.append(prereq.strip())

                all_prerequisites = [
                    s for s in prerequisites if len(s.strip()) > 1]

                prerequisites = []
                if not ordering:
                    prerequisites = all_prerequisites
                else:
                    for a in range(len(ordering)):
                        if '(' in ordering[a]:
                            prerequisites.append(ordering[a])
                        elif ')' in ordering[a]:
                            prerequisites.append(ordering[a])
                        else:
                            if a == 0 or '(' in ordering[a - 1]:
                                prerequisites.append(all_prerequisites.pop(0))
                            prerequisites.append(ordering[a])
                            if a == len(ordering) - 1 or '(' not in ordering[a + 1]:
                                prerequisites.append(all_prerequisites.pop(0))

            elif "Corequisites" in description:

                for a in soup.find_all('a'):
                    corequisites.append(a.text.strip())
                corequisites = [s for s in corequisites if len(s) > 1]

        concurrent_prerequisites = False
        if "taken concurrently" in full_prerequisite_description:
            concurrent_prerequisites = True

        level_undergrad = False
        level_graduate = False
        for a in level:
            if 'Undergraduate' in a:
                level_undergrad = True
            if 'Graduate' in a:
                level_graduate = True
        if len(credit_hours) == 1:
            min_credit_hours = credit_hours[0]
            max_credit_hours = credit_hours[0]
        else:
            min_credit_hours = credit_hours[0]
            max_credit_hours = credit_hours[1]

        stop_words = ['e.g.', 'multiple', 'improve', 'focusing', 'many', 'do', 'two', 'given',
                      'properties', 'needed', 'needs', 'among', 'settings.', 'must',
                      'covered', 'area', 'continue', 'examples', 'skills,', 'support',
                      'several', 'forms', 'and/or', 'semester', 'when', 'students.',
                      'challenges', 'important', 'assessment', 'our', 'required',
                      'but', 'topic', 'during', 'upon', 'while', 'has', 'necessary',
                      'become', 'appropriate', 'accompanies', 'own', 'based', 'relevant',
                      'prepare', 'apply', 'addresses', 'supervision', 'areas', 'some', 'depends',
                      'those', 'focus', 'course.', 'them', 'topic.', 'not', 'understand', 'each',
                      'into', 'key', 'student’s', 'all', 'approaches', 'what', 'more', 'seeks',
                      'in-depth', 'supervision.', 'considers', 'provide', 'instructor.', 'can',
                      'continues', 'chosen', 'emphasis', 'different', 'applications', 'who', 'may',
                      'requires', 'its', 'they', 'about', 'using', 'between', 'have', 'understanding',
                      'designed', 'discusses', 'includes', 'courses', 'taken', 'use', 'project', 'be',
                      'emphasizes', 'these', 'which', 'study', 'well', 'various', 'also', 'faculty',
                      'student', 'this', 'develop', 'studies', 'skills', 'provides', 'explores',
                      'through', 'such', 'including', 'introduces', 'at', 'other', 'covers', 'include',
                      'by', 'how', 'or', 'is', 'focuses', 'examines', 'from', 'are', 'their', 'that',
                      'opportunity', 'with', 'offers', 'as', 'an', 'for', 'on', 'students', 'a',
                      'in', 'to', 'of', 'the', 'and', 'student.', 'very', 'one', 'two', 'topics']

        course_description_keywords = [
            word.lower() for word in course_description.split() if word.lower() not in stop_words]
        course_description_keywords = ''.join(
            c for c in ' '.join(course_description_keywords) if c not in ',.();"')
        course_description_keywords = course_description_keywords.replace(
            '/', ' ')

        session = Session()

        course = models.Course(course_name=name,
                               department_id=department_id,
                               course_number=course_number,
                               course_url=url,
                               course_description=course_description,
                               course_description_keywords=course_description_keywords,
                               concurrent_prerequisites=concurrent_prerequisites,
                               prerequisites=prerequisites,
                               corequisites=corequisites,
                               restrictions=restrictions,
                               is_undergraduate=level_undergrad,
                               is_graduate=level_graduate,
                               min_credit_hours=min_credit_hours,
                               max_credit_hours=max_credit_hours,
                               full_prerequisite_description=full_prerequisite_description)

        session.merge(course)
        try:
            session.commit()
        except Exception as e:
            app.logger.error(
                'Error when storing course ' + repr(course) + '\n' + repr(e))
            session.rollback()

        for a in course_attributes:
            a = re.sub(r'\bLvl\b', 'Level', a)
            a = re.sub(r'\bComp\b', 'Comparative', a)
            a = re.sub(r'\bStdy\b', 'Study', a)
            a = re.sub(r'\bMath/Anly\b', 'Math/Analytical', a)
            a = re.sub(r'\bThink\b', 'Thinking', a)
            a = re.sub(r'\bScience/Tech\b', 'Science/Technology', a)
            a = re.sub(r'\bIntsv in Majr\b', 'Intensive in Major', a)
            a = re.sub(r'\bYr\b', 'Year', a)
            a = re.sub(
                r'\bAdv Writ Dscpl\b', 'Advanced Writing in the Disciplines', a)
            a = re.sub(r'\bExpress/Innov\b', 'Expression/Innovation', a)
            a = re.sub(r'\bFormal/Quant\b', 'Formal/Quantitative', a)
            a = re.sub(r'\bEthical&Pol\b', 'Ethical and Policial', a)
            a = re.sub(r'\bPrspctv\b', 'Prospective', a)
            a = re.sub(r'\bComm\b', 'Communication', a)
            a = re.sub(r'\bCol\b', 'College', a)
            a = re.sub(r'\bEthical&Pol\b', 'Ethical and Political', a)
            a = re.sub(r'\bPrspctv\b', 'Perspectives', a)
            a = re.sub(r'\bWritten Comm\b', 'Written Communication', a)
            a = a.replace('/', ' and ')
            a = a.replace('&', 'and')

            if 'NUpath' in a or 'NU Core' in a or 'CPS ' in a or 'Faculty Led Study Abroad' in a or 'Honors' in a or 'Three Seas Program' in a or 'Service Learning' in a:
                searchable = True
            else:
                searchable = False

            attribute = models.CourseAttribute(
                department_id=department_id, course_number=course_number, attribute=a, is_searchable=searchable)

            session.merge(attribute)
            try:
                session.commit()
            except Exception as e:
                app.logger.error(
                    'Error when storing attribute ' + repr(attribute) + '\n' + repr(e))
                session.rollback()
        session.close()
    except AttributeError:
        raise
    except Exception as e:
        app.logger.error(
            'Error when parsing course page: ' + webpage.prettify() + '\n' + repr(e))


def scrape_schedule(number_of_most_recent_terms=5):
    """
    Find all class scheduling information from NEU in parallel. This includes information such as
    professors, date&time, and location for each class

    Can set a lower term and upper term bound by specifying the their respective term ids that can
    be found on myNEU.
    """
    try:
        term_ids = models.Term.query.with_entities(models.Term.term_id).all()
        term_ids = [term_id[0] for term_id in term_ids]
        # Processes only the specified amount of terms
        term_ids.sort()
        if number_of_most_recent_terms < len(term_ids):
            number_of_most_recent_terms = number_of_most_recent_terms * -1
            term_ids = term_ids[number_of_most_recent_terms:]
    except Exception as e:
        app.logger.error('Error with retrieving terms ' + '\n' + repr(e))

    try:
        # Find all department IDs to look for classes within
        department_ids = models.Department.query.with_entities(
            models.Department.department_id).all()
        department_ids = [department_id[0] for department_id in department_ids]
    except Exception as e:
        app.logger.error('Error with retrieving terms ' + '\n' + repr(e))

    try:
        p = multiprocessing.Pool()

        for ID in sorted(term_ids):
            p.starmap(find_schedule_page, zip(department_ids, repeat(ID)))
    except Exception as e:
        app.logger.error('Error with parallel scraping of schedule ' +
                         '\n' + str(term_ids) + '\n' + str(department_ids) + '\n' + repr(e))


def find_schedule_page(department_id, term_id):
    """
    Finds links to all class sections given a term_id and a department_id
    """

    app.logger.info(
        'Finding schedule pages ' + department_id + '\t' + str(term_id))

    try:
        data = ("sel_day=dummy"
                "&STU_TERM_IN=" + str(term_id) +
                "&sel_subj=dummy"
                "&sel_attr=dummy"
                "&sel_schd=dummy"
                "&sel_camp=dummy"
                "&sel_insm=dummy"
                "&sel_ptrm=dummy"
                "&sel_levl=dummy"
                "&sel_instr=dummy"
                "&sel_seat=dummy"
                "&p_msg_code=UNSECURED"
                "&sel_crn="
                "&sel_subj=" + department_id +
                "&sel_crse="
                "&sel_title="
                "&sel_attr=%25"
                "&sel_levl=%25"
                "&sel_schd=%25"
                "&sel_insm=%25"
                "&sel_from_cred="
                "&sel_to_cred="
                "&sel_camp=%25"
                "&sel_ptrm=%25"
                "&sel_instr=%25"
                "&begin_hh=0"
                "&begin_mi=0"
                "&begin_ap=a"
                "&end_hh=0"
                "&end_mi=0"
                "&end_ap=a")

        session = requests.Session()
        session.mount(
            "https://", requests.adapters.HTTPAdapter(max_retries=10))
        response = session.post(
            "https://wl11gp.neu.edu/udcprod8/NEUCLSS.p_class_search", data=data)
    except Exception as e:
        app.logger.error('Error when accessing schedule page for term: ' +
                         str(term_id) + ' and department ' + department_id + '\n' + repr(e))

    process_schedule_page(response.text, term_id, department_id)


def process_schedule_page(webpage, term_id, department_id):
    """
    Processes a schedule page, extracts all relevant information, and stores it.

    Input is the raw webpage html, the term_id of the class schedule, and the department_id
    """
    app.logger.info(
        'Processesing schedule page ' + str(department_id) + '\t' + str(term_id))
    try:
        soup = BeautifulSoup(webpage, 'html5lib')
        soup = (soup.find("table", {"class": "datadisplaytable"}).tbody)
        for element in soup:
            if hasattr(element, 'text') and element.find('th', {'class': "ddtitle", 'scope': "colgroup"}):
                # Fix for splitting only hyphens that separate different parts in the title, such as
                # Introduction to Engineering Co-op Education - 10032 - EECE 2000 -
                # 03- (Boston) - Credits 1
                title = element.text.replace('- ', ' -').split(' -')
                num_title_elements = len(title)
                if num_title_elements > 6:
                    # Rebuilds titles that have hyphens
                    for i in range(1, num_title_elements - 5):
                        title[0] += "-" + title[1]
                        title.pop(1)
                # Fix annoying appreviations
                course_name = title[0] \
                    .replace('ST:', '') \
                    .replace('ST', '') \
                    .replace('Spcl ', 'Special ') \
                    .replace('Spec ', 'Special ') \
                    .replace('Adv. ', 'Advanced ') \
                    .replace('Adv ', 'Advanced ') \
                    .replace('Mgmt ', 'Management ') \
                    .replace('Fund. ', 'Fundamentals ') \
                    .strip()
                # Extract parts of title
                crn = int(title[1])
                course_number = int(title[2].split()[1])
                section = title[3].strip()
                location = title[4].strip()
                credit_hours = re.findall(r'\d+\.*\d*', title[5])
                credit_hours = [float(i) for i in credit_hours]
            # Extract professor information
            all_professor_names = []
            if hasattr(element, 'text') and element.find('td', {'class': "dddefault"}):
                secondary_professor_names = []
                if "Instructors:" in element.text and "(P)" in element.text:
                    all_professor_names = [unidecode(string.capwords(a.strip())) for a in element.text.split(
                        'Instructors:')[1].split('Schedule Type:')[0].replace('(P)', '').strip().split(',')]
                    professor_name = all_professor_names[0]
                    if len(all_professor_names) > 1:
                        secondary_professor_names = all_professor_names[1:]
                else:
                    professor_name = "N/A"
                    all_professor_names = ["N/A"]
            # Extract scheduling information
            if hasattr(element, 'text') and element.find('table', {'class': "datadisplaytable"}):
                class_date_start_end = []
                class_times = []
                day_of_week = []
                for table in element.find('table', {'class': "datadisplaytable"}):
                    if hasattr(table, 'text') and "Class" in table.text:
                        for table_row in table.text.split("\n\n"):
                            # Extract all time information about the class
                            if "Class" in table_row:
                                table_entries = table_row.split("\n")
                                table_entries.pop(0)
                                class_type = str(table_entries[0]).strip()
                                # If a valid time
                                if "TBA" not in table_entries[1]:
                                    class_times.append([datetime.strptime(table_entries[1].split('-')[0].strip(), '%I:%M %p')
                                                        .time(), datetime.strptime(table_entries[1].split('-')[1].strip(), '%I:%M %p').time()])
                                    day_of_week.append(
                                        table_entries[2].strip())
                                else:
                                    # Non existing time
                                    class_times.append(
                                        [datetime(1900, 1, 1, 0, 0).time(), datetime(1900, 1, 1, 0, 0).time()])
                                    day_of_week.append("TBA")

                                location = table_entries[3].strip()
                                class_date_start_end.append([datetime.strptime(table_entries[4].split('-')[0].strip(), '%b %d, %Y'),
                                                             datetime.strptime(table_entries[4].split('-')[1].strip(), '%b %d, %Y')])

                                capacity = int(table_entries[5].strip())
                                seats_taken = int(table_entries[6].strip())
                                waitlist = int(table_entries[7].strip())
                                seats_left = int(table_entries[8].strip())

                                if "N/A" not in table_entries[9]:
                                    room_size = int(table_entries[9].strip())
                                else:
                                    room_size = -1

                if len(credit_hours) == 1:
                    min_credit_hours = credit_hours[0]
                    max_credit_hours = credit_hours[0]
                else:
                    min_credit_hours = credit_hours[0]
                    max_credit_hours = credit_hours[1]

                section = models.Section(department_id=department_id,
                                         course_number=course_number,
                                         crn=crn,
                                         section_id=section,
                                         location=location,
                                         min_credit_hours=min_credit_hours,
                                         max_credit_hours=max_credit_hours,
                                         section_type=class_type,
                                         term_id=term_id,
                                         capacity=capacity,
                                         seats_taken=seats_taken,
                                         seats_left=seats_left,
                                         room_size=room_size,
                                         waitlist=waitlist,
                                         professor_name=professor_name,
                                         course_name=course_name,
                                         secondary_professor_names=secondary_professor_names)
                session = Session()
                for professor_name in all_professor_names:
                    # Add professor to professor database
                    professor = models.Professor(professor_name=professor_name)
                    session.merge(professor)
                    try:
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        app.logger.error(
                            'Error storing professor: ' + '\n' + repr(professor) + '\n' + repr(e))

                session.merge(section)
                try:
                    session.commit()
                except Exception as e:
                    session.rollback()
                    app.logger.error(
                        'Error storing section: ' + '\n' + repr(section) + ' ' + repr(e))

                for i in range(len(class_times)):
                    section_time = models.SectionTime(crn=crn,
                                                      start_date=class_date_start_end[
                                                          i][0],
                                                      end_date=class_date_start_end[
                                                          i][1],
                                                      start_time=class_times[
                                                          i][0],
                                                      end_time=class_times[
                                                          i][1],
                                                      term_id=term_id,
                                                      day_of_week=day_of_week[i])
                    session.merge(section_time)
                    try:
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        app.logger.error(
                            'Error storing section time: ' + '\n' + repr(section_time) + '\n' + repr(e))
                session.close()
    except Exception as e:
        app.logger.error(
            'Error when parsing schedule page: ' + webpage + '\n' + repr(e))


def initiate_trace_question_key():
    trace_question_key = {
        0: "All responses are completely anonymous, and participation in the evaluation process is expected. " +
           "However, you are permitted to opt out of completing this questionnaire by selecting 'Opt Out.'",
        1: "The syllabus helped me to learn.",
        2: "The textbook(s) helped me to learn.",
        3: "The materials posted online, including Blackboard, helped me to learn.",
        4: "The out-of-class assignments and fieldwork helped me to learn.",
        5: "The lectures helped me to learn.",
        6: "The in-class discussions and activities helped me to learn.",
        7: "The classroom technology helped me to learn.",
        8: "The number of hours per week I devoted to this course including lectures, discussions, homework, reading, projects, assignments and tests.",
        9: " I found this course intellectually challenging.",
        10: "I learned a lot in this course.",
        11: "I learned to apply course concepts and principles.",
        12: "I developed additional skills in expressing myself orally and in writing.",
        13: "I learned to analyze and evaluate ideas, arguments, and points of view.",
        14: "The instructor possessed the basic communications skills necessary to teach the course.",
        15: "The instructor clearly communicated ideas and information.",
        16: "The instructor clearly stated the objectives of the course.",
        17: "The instructor covered what was stated in the course objectives and syllabus.",
        18: "The instructor came to class prepared to teach.",
        19: "The instructor used class time effectively.",
        20: "The instructor provided sufficient feedback.",
        21: "The instructor fairly evaluated my performance.",
        22: "The instructor is someone I would recommend to other students.",
        23: "The instructor treated students with respect.",
        24: "The instructor acknowledged and took effective action when students did not understand the material.",
        25: "The instructor was available to assist students outside of class.",
        26: "The instructor displayed enthusiasm for the course.",
        27: "What is your overall rating of this instructor's teaching effectiveness?"
    }

    session = Session()
    for key, val in trace_question_key.items():
        trace_survey_question_key = models.TraceSurveyQuestionKey(
            key_id=key, trace_survey_question=val)
        session.merge(trace_survey_question_key)
        try:
            session.commit()
        except Exception as e:
            app.logger.error('Error when storing trace survey ' +
                             repr(trace_survey_question_key) + '\n' + repr(e))
            session.rollback()
    session.close()


def scrape_trace_URLs(cookie):
    """
    Scrapes trace page for all trace survey links and stores them along with their professor, course number, term id, and department id
    """
    headers = {
        "Cookie": cookie
    }
    try:
        session = requests.Session()
        session.mount(
            "https://", requests.adapters.HTTPAdapter(max_retries=10))
        response = session.post(
            "https://prod-web.neu.edu/wasapp/TRACE25/secure/search.do", headers=headers, data="survey.surveyID=0&instructor.nuid=&department.deptId=")
    except Exception as e:
        app.logger.error('Error when accessing url page \n' + repr(e))
    try:
        soup = BeautifulSoup(response.text, 'html5lib').find(
            "table", {"class": "classic"}).tbody
        # Split by row of text
        for row in soup.find_all('tr'):
            # Split by columns within rows
            columns = row.find_all('td')
            # Check if any elements in colum
            if len(columns) > 0:
                # Term name e.g. Fall 2014
                term = columns[0].text.strip()
                # Professor name : First M. Last
                professor = unidecode(
                    columns[1].text.strip()).replace("`", "'")
                # Some professors have period after middle initial, some don't
                # whelp
                if len(professor.split(',')[1].strip().split()[-1].strip()) == 1:
                    professor = professor.split(
                        ',')[1].strip() + '. ' + professor.split(',')[0].strip()
                else:
                    professor = professor.split(
                        ',')[1].strip() + ' ' + professor.split(',')[0].strip()
                course = columns[3].text.strip()
                # Course number e.g. 1000
                course_number = course[-4:]
                # Course department e.g. ACCT
                department_id = course.replace(course_number, '')
                course_number = int(course_number)

                url = 'https://prod-web.neu.edu/' + \
                    columns[3].find('a', href=True)['href']
                # Section of class that term e.g. 01, 02, 03...
                section = columns[5].text.strip()

                def find_professor(first_name, last_name):
                    return models.Professor.query.filter(
                        and_(models.Professor.professor_name.ilike(first_name),
                             models.Professor.professor_name.ilike(last_name))
                    ).all()

                first_name = professor.split()[0]
                last_name = professor.split()[-1]

                professor_new = find_professor(
                    "%" + first_name + "%", "%" + last_name + "%")

                if not professor_new:
                    professor_new = find_professor(
                        first_name[0] + "%", "%" + last_name + "%")
                    if not professor_new or len(professor_new) > 1:
                        professor_new = find_professor(
                            first_name[0:2] + "%", "%" + last_name + "%")
                        if not professor_new or len(professor_new) > 1:
                            professor_new = find_professor(
                                first_name[0:3] + "%", "%" + last_name + "%")
                            if not professor_new or len(professor_new) > 1:
                                professor_new = find_professor(
                                    first_name + "%", "%" + last_name[-1] + "%")
                                if not professor_new or len(professor_new) > 1:
                                    professor_new = find_professor(
                                        first_name + "%", "%" + last_name[-2:] + "%")
                                    if not professor_new or len(professor_new) > 1:
                                        professor_new = find_professor(
                                            first_name + "%", "%" + last_name[-3:] + "%")

                elif len(professor_new) > 1:
                    professor_new = find_professor(
                        first_name + "%", "%" + last_name)
                    if len(professor_new) > 1:
                        professor_new = find_professor(
                            "%" + first_name + ' ' + professor.split()[1].split()[0] + "%", "%" + last_name + '%')
                        if len(professor_new) > 1:
                            professor_new = find_professor(
                                first_name + ' ' + professor.split()[1].split()[0] + "%", "%" + last_name)
                            if len(professor_new) > 1:
                                professor_new = find_professor(
                                    first_name + ' ' + professor.split()[1].split()[0:2] + "%", "%" + last_name)

                if len(professor_new) == 1:
                    professor_new = professor_new[0]

                    trace = models.TraceSurvey(department_id=department_id,
                                               course_number=course_number,
                                               professor_name=professor_new.professor_name,
                                               trace_survey_url=url,
                                               section_id=section,
                                               term_name=term)

                    app.logger.info('Storing ' + repr(trace))

                    session = Session()
                    session.merge(trace)
                    try:
                        session.commit()
                    except Exception as e:
                        app.logger.error(
                            'Error when storing trace survey ' + repr(trace) + '\n' + repr(e))
                        session.rollback()
                    session.close()
                elif len(professor_new) > 1:
                    app.logger.warning(
                        'Multiple matching professors ' + professor + ' ' + url)
                elif not professor_new:
                    app.logger.warning(
                        'No matching professors ' + professor + ' ' + url)
    except Exception as e:
        app.logger.error('Error when parsing term page ' + '\n' + repr(e))


def scrape_trace_URL_information_parallel(cookie):
    """
    Scrapes information from trace urls in parallel
    """
    headers = {
        "Cookie": cookie
    }
    try:
        urls = models.TraceSurvey.query.filter(models.TraceSurvey.survey_result == None).with_entities(
            models.TraceSurvey.trace_survey_url).all()
        urls = [url[0] for url in urls]
        p = multiprocessing.Pool()
        p.map(access_trace_URL_page, zip(urls, repeat(headers)))
    except Exception as e:
        app.logger.error(
            'Error with parallel scraping of trace surveys ' + '\n' + repr(e))


def access_trace_URL_page(url, headers):
    """
    Opens the url for a trace page
    """
    app.logger.info('Accessing trace url: ' + url)
    try:
        session = requests.Session()
        session.mount(
            "https://", requests.adapters.HTTPAdapter(max_retries=10))
        response = session.post(url, headers=headers)
    except Exception as e:
        app.logger.error(
            'Error when accessing url page ' + url + '\n' + repr(e))

    proccess_trace_page(response.text, url, headers)


def proccess_trace_page(webpage, url, headers):
    """
    Extracts information from a trace webpage and stores it
    """
    try:
        soup = BeautifulSoup(webpage, 'html5lib').find(
            "div", {"id": "leftcolumnBig"})
        # Find all tables in the page
        tables = soup.find_all("table")
        # Find all the ratings in the page
        ratings = []
        for table in tables:
            ratings.append([int(s) for s in table.text.split() if s.isdigit()])

        def format_response_parts(rating, index):
            if index == 0:
                return {"No Response": rating[0],
                        "Will Participate": rating[1],
                        "Choose not to participate": rating[2]}
            elif index == 8:
                return {"1-4": rating[0],
                        "5-8": rating[1],
                        "9-12": rating[2],
                        "13-16": rating[3],
                        "17-29": rating[4],
                        "No Response": rating[5]}
            elif index == 27:
                return {5: rating[0],
                        4: rating[1],
                        3: rating[2],
                        2: rating[3],
                        1: rating[4],
                        0: rating[5]}
            else:
                return {5: rating[0],
                        4: rating[1],
                        3: rating[2],
                        2: rating[3],
                        1: rating[4],
                        0: rating[5],
                        "N/A": rating[6]}

        survey = {}
        for i in range(len(ratings)):
            survey[i] = format_response_parts(ratings[i], i)

        session = requests.Session()

        # Find links to course and professor comments
        links_in_page = soup.find_all("a")
        links_to_parse = []
        for link in links_in_page:
            if "View Responses for question" in link.text:
                links_to_parse.append(
                    "https://prod-web.neu.edu" + link['href'].split('\'')[1])

        if links_to_parse:
            response = session.post(links_to_parse[0], headers=headers)
            course_comments = parse_trace_comments(response.text)

            response = session.post(links_to_parse[1], headers=headers)
            professor_comments = parse_trace_comments(response.text)

            survey["course_comments"] = course_comments
            survey["professor_comments"] = professor_comments
        trace = models.TraceSurvey(trace_survey_url=url,
                                   survey_result=json.dumps(survey))
        session = Session()
        session.merge(trace)
        try:
            session.commit()
        except Exception as e:
            app.logger.error(
                'Error when storing trace survey ' + repr(trace) + '\n' + repr(e))
            session.rollback()
        session.close()
    except Exception as e:
        app.logger.error(
            'Error when parsing trace webpage ' + webpage + '\n' + repr(e))


def parse_trace_comments(webpage):
    """
    Parses comments page of trace and returns comments
    """
    soup = BeautifulSoup(webpage, 'html5lib')
    page_text = soup.find_all("p")

    comments = []
    for t in page_text:
        comments.append(t.text.strip())
    return [s for s in comments if len(s) > 1 and "Close window" not in s]


def find_professor_summaries():
    """
    Determine professor summaries by examing trace evaulations and coming up with a summary score
    """
    try:
        professors = models.Professor.query.filter(
            models.Professor.general_score == None).all()

        for professor in professors:
            professor_name = professor.professor_name

            if professor_name == "N/A":
                continue

            def find_score(category, results):
                return (results[category]['5'] * 5 +
                        results[category]['4'] * 4 +
                        results[category]['3'] * 3 +
                        results[category]['2'] * 2 +
                        results[category]['1']), \
                    (results[category]['5'] +
                     results[category]['4'] +
                     results[category]['3'] +
                     results[category]['2'] +
                     results[category]['1'])

            trace_surveys = models.TraceSurvey.query.filter(
                models.TraceSurvey.professor_name == professor_name
            ).all()

            if not trace_surveys:
                continue

            trace_scores = {}
            # The instructor possessed the basic communications skills
            # necessary to teach the course.
            trace_scores['14'] = {}
            trace_scores['14']['multiplier'] = 3
            # The instructor clearly communicated ideas and information.
            trace_scores['15'] = {}
            trace_scores['15']['multiplier'] = 2
            # The instructor clearly stated the objectives of the course.
            trace_scores['16'] = {}
            trace_scores['16']['multiplier'] = 1
            # The instructor came to class prepared to teach.
            trace_scores['18'] = {}
            trace_scores['18']['multiplier'] = 2
            # The instructor used class time effectively.
            trace_scores['19'] = {}
            trace_scores['19']['multiplier'] = 2
            # The instructor provided sufficient feedback.
            trace_scores['20'] = {}
            trace_scores['20']['multiplier'] = 1
            # The instructor fairly evaluated my performance.
            trace_scores['21'] = {}
            trace_scores['21']['multiplier'] = 3
            # The instructor is someone I would recommend to other students.
            trace_scores['22'] = {}
            trace_scores['22']['multiplier'] = 6
            # The instructor treated students with respect.
            trace_scores['23'] = {}
            trace_scores['23']['multiplier'] = 1
            # The instructor acknowledged and took effective action when
            # students did not understand the material.
            trace_scores['24'] = {}
            trace_scores['24']['multiplier'] = 2
            # The instructor was available to assist students outside of class.
            trace_scores['25'] = {}
            trace_scores['25']['multiplier'] = 2
            # The instructor displayed enthusiasm for the course.
            trace_scores['26'] = {}
            trace_scores['26']['multiplier'] = 3
            # What is your overall rating of this instructor's teaching
            # effectiveness?
            trace_scores['27'] = {}
            trace_scores['27']['multiplier'] = 6

            for trace_type in trace_scores:
                trace_scores[trace_type]['score'] = 0
                trace_scores[trace_type]['count'] = 0

            for survey in trace_surveys:
                results = json.loads(survey.survey_result)

                for trace_type in trace_scores:
                    score = find_score(trace_type, results)
                    trace_scores[trace_type]['score'] += score[0]
                    trace_scores[trace_type]['count'] += score[1]

            total = 0
            total_score = 0
            for trace_type in trace_scores:
                if trace_scores[trace_type]['count']:
                    trace_scores[trace_type]['total_score'] = trace_scores[trace_type]['score'] / trace_scores[
                        trace_type]['count']
                    total_score += trace_scores[trace_type]['total_score'] * \
                        trace_scores[trace_type]['multiplier']
                    total += trace_scores[trace_type]['multiplier']

            if total:
                professor = models.Professor(
                    professor_name=professor_name, general_score=(total_score/total * 200), all_scores=json.dumps(trace_scores))

                session = Session()
                session.merge(professor)
                try:
                    session.commit()
                except Exception as e:
                    app.logger.error(
                        'Error when storing trace survey ' + repr(professor) + '\n' + repr(e))
                    session.rollback()
                session.close()
    except Exception as e:
        app.logger.error('Error when finding professor summaries\n' + repr(e))
