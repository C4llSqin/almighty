from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from formLogic import *
import re

def make_webdriver() -> webdriver.Firefox:
    #todo: make this read a json, and choose profiles.
    return webdriver.Firefox()

def find_list(webdriver: webdriver.Firefox):
    whole_html = webdriver.page_source # literaly the whole html as plain text
    section_start = re.search(r"<div class=\"(.{3,6})\" role=\"list\">", whole_html)
    section_start_class_name = section_start.group(1)
    return webdriver.find_element(By.CLASS_NAME, section_start_class_name)

def find_section_title(section_element): ...

def fillout_section(webdriver: webdriver.Firefox, section: Section):
    section_element = find_list(webdriver)

def fillout_form(webdriver: webdriver.Firefox, form: Form) -> tuple[int, int]:
    # webdriver.find_element(By.)
    return (0, 0)

def machine_learning(webdriver: webdriver.Firefox, form: Form): 
    ...

def first_time_scan(webdriver: webdriver.Firefox) -> Form:
    form = Form()
    while True: #TODO: add logic to prevent trying to add the form results as an section
        section_element = find_list(webdriver)
        ...
        section = Section()
        form.sections.append(section)


a = make_webdriver()
input(a)
a.close()