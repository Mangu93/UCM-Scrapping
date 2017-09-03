# -*- coding: utf-8 -*-

import errno
import os
import pprint
import shutil
from pathlib import Path
import requests
from bs4 import BeautifulSoup

__author__ = 'Adrian Marin'

BASE_URL = 'http://ocw.uc3m.es/cursos'
EXTENDED = BASE_URL + '?b_start:int=20'
ACTUAL_SECTION = ''
BASE_CWD = os.getcwd()
SEARCH_FOR_WORDS = (
    "Material de clase", 'Ejercicio', 'Prácticas', 'Pruebas de evaluación ', 'Exercises', 'Lecture Notes', 'Labs',
    'Evaluation Tests')


def main_processing():
    base_req = requests.get(BASE_URL)
    extended_req = requests.get(EXTENDED)
    if base_req.status_code == 200 and extended_req.status_code == 200:
        base_html = BeautifulSoup(base_req.text, "html.parser")
        extended_html = BeautifulSoup(extended_req.text, "html.parser")
        base_categories = base_html.find_all('table', {'class': 'division-listing'})
        extended_categories = extended_html.find_all('table', {'class': 'division-listing'})
        for extended_category in extended_categories:
            base_categories.append(extended_category)
        to_print = [str(index) + ": " + category.find('a')['name'] for index, category in enumerate(base_categories)]
        print("CATEGORIAS")
        pprint.pprint(to_print)
        print("INTRODUCE EL NUMERO DE LA QUE QUIERES INTRODUCIR. PULSA ENTER SIN INTRODUCIR NADA PARA DESCARGAR TODO")
        try:
            user_input = getnumber()
        except:
            user_input = None
        if user_input == "":
            for i, entry in enumerate(base_categories):
                process_choice(entry, all_values=True)
        else:
            entry = base_categories[int(user_input)]
            process_choice(entry)


# noinspection PyPep8
def process_choice(entry, all_values=False):
    filtered_entries = [filtered_entry for filtered_entry in entry.find_all('a', href=True) if
                        not 'img src' in filtered_entry.__str__()][
                       1:]
    courses_to_print = [str(index) + ": " + course['href'].split('/')[-1].upper() for index, course in
                        enumerate(filtered_entries)]
    if all_values:
        for link in filtered_entries:
            process_course(link['href'])
    else:
        print("CURSOS")
        pprint.pprint(courses_to_print)
        print("INTRODUCE UN NUMERO PARA DESCARGAR EL CURSO. PULSA ENTER SIN INTRODUCIR NADA PARA DESCARGAR TODOS")
        try:
            user_input = getnumber()
        except:
            user_input = None
        if user_input == "":
            for link in filtered_entries:
                process_course(link['href'])
        else:
            entry = filtered_entries[int(user_input)]
            process_course(entry['href'])


def process_course(link):
    try:
        course_request = requests.get(link)
        if course_request.status_code == 200:
            course_html = BeautifulSoup(course_request.text, "html.parser")
            create_directory(course_html.title.string.split('— ')[0])
            course_links = course_html.find_all('dd', {'class': 'portletItem'})

            for entry_link in enumerate(course_links):
                entry_name = entry_link[1].getText()
                global SEARCH_FOR_WORDS
                if any(word in entry_name for word in SEARCH_FOR_WORDS):
                    process_section(entry_link[1].find('a')['href'])
            print("Course downloaded")
    except requests.exceptions.ConnectionError:
        print("Skipped course because of timeout")


def process_section(link_section):
    try:
        section_request = requests.get(link_section)
        if section_request.status_code == 200:
            section_html = BeautifulSoup(section_request.text, "html.parser")
            section_links = section_html.find_all('a', href=True)
            links_with_files = [link for link in enumerate(section_links) if 'pdf' in link[1]['href']]
            for section_link in links_with_files:
                download_pdf(section_link[1]['href'][:-4])
            print("Section downloaded")
    except requests.exceptions.ConnectionError:
        print("Skipped section because of timeout")


def download_pdf(pdf_link):
    global ACTUAL_SECTION
    global BASE_CWD
    try:
        pdf_request = requests.get(pdf_link + 'at_download/file', stream=True)
        path = Path(os.path.join(os.getcwd(), 'courses', ACTUAL_SECTION))
        os.chdir(path.__str__())
        name_file = os.path.basename(os.getcwd()) + str(
            len([name for name in os.listdir('.') if os.path.isfile(name)])) + ".pdf"[-30:]
        with open(name_file, 'wb') as fpdf:
            fpdf.write(pdf_request.content)
        os.chdir(BASE_CWD)
        print("Downloaded %s" % name_file)
    except requests.exceptions.ConnectionError:
        print("Skipped file because of timeout")


# Auxiliary methods
def create_directory(link):
    try:
        global ACTUAL_SECTION
        ACTUAL_SECTION = link
        os.makedirs('courses/' + link)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            pass


def getnumber():
    while True:
        number = input("Numero: ")
        if number.isdigit() or number == "":
            return number


if __name__ == "__main__":
    main_processing()
