from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from formLogic import *
import re

def make_webdriver() -> webdriver.Firefox:
    #todo: make this read a json, and choose profiles.
    return webdriver.Firefox()

def fillout_section(webdriver: webdriver.Firefox, section: Section):
    whole_html = webdriver.page_source # literaly the whole html as plain text
    section_start = re.search(r"<div class=\"(.{3,6})\" role=\"list\">", whole_html)
    section_start_class_name = section_start.group(1)
    section_element = webdriver.find_element(By.CLASS_NAME, section_start_class_name)
    

def fillout_form(webdriver: webdriver.Firefox, form: Form) -> tuple[int, int]:
    # webdriver.find_element(By.)
    return (0, 0)

def machine_learning(webdriver: webdriver.Firefox, form: Form): pass

def first_time_scan(webdriver: webdriver.Firefox) -> Form:
    form = Form()
    


a = make_webdriver()
input(a)
a.close()