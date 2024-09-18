from selenium import webdriver
from selenium.webdriver.remote import webelement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from formLogic import *
import re
import json

XPATH_LISTITEM_POINTVALUE = "div/div/div[1]/div[2]"
XPATH_LISTITEM_STR_INPUT = "div/div/div[2]/div/div[1]/div/div[1]/input"
AAAAAAAAAAAAAAAAAAA = "/html/body/div/div[3]/form/div[2]/div/div[2]/div[3]"

def make_webdriver() -> webdriver.Firefox:
    #todo: make this read a json, and choose profiles.
    ffOptions = webdriver.FirefoxOptions()
    ffOptions.add_argument("-profile")
    with open("profilepath.txt") as f:
        ffOptions.add_argument(f.read())
    return webdriver.Firefox(ffOptions)

def try_find_element(web_element: webelement.WebElement, xpath: str):
    try:
        return web_element.find_element(By.XPATH, xpath)
    except:
        return None

def find_list(web_driver: webdriver.Firefox):
    whole_html = web_driver.page_source # literaly the whole html as plain text
    section_start = re.search(r"<div class=\"(.{3,6})\" role=\"list\">", whole_html)
    if section_start == None:
        breakpoint()
    section_start_class_name = section_start.group(1)
    return web_driver.find_element(By.CLASS_NAME, section_start_class_name)

def fillout_section(web_driver: webdriver.Firefox, section: Section):
    section_element = find_list(web_driver)
    for listitem in section_element.find_elements(By.XPATH, '*'):
        child_item = listitem.find_element(By.XPATH, "div")
        if listitem.get_dom_attribute("role") == "listitem":
            data_pram_str = child_item.get_dom_attribute("data-params")
            if data_pram_str:
                #This is a question, get the `Question` from the `Section` and then get the awnser and apply the awnser.
                data_pram_json = json.loads('['+data_pram_str[4:])
                question_name = data_pram_json[0][1]
                question_type = data_pram_json[0][3]
            
                question = section.search_by_question_title(question_name)
                assert(question != None, "Missed a Question.")
                awnser = question.get_awnser()
                if question_type == 0 or question_type == 1:
                    text_box = listitem.find_element(By.XPATH, XPATH_LISTITEM_STR_INPUT)
                    text_box.click()
                    text_box.send_keys(awnser)
                elif question_type == 2 or question_type == 4:
                    #TODO: look at data_pram_json and determin where the buttons are.
                    # And then click on the buttons that are in the awnsers array.
                    ...
                    
            
        elif child_item != None and child_item.get_dom_attribute("data-user-email-address") != None:
            #Email Checkbox, click on it
            #TODO: find the XPATH to the actual clickable area.
            listitem.click()
        else:
            print("Not a Question, don't know what it could be")

def fillout_form(web_driver: webdriver.Firefox, form: Form) -> tuple[int, int]:
    # webdriver.find_element(By.)
    return (0, 0)

def machine_learning(web_driver: webdriver.Firefox, form: Form): 
    #TODO analize the results page to determin which questions are correct.
    ...

def scan_listitem(web_element: webelement.WebElement, section: Section):
    child_item = web_element.find_element(By.XPATH, "div")
    if web_element.get_dom_attribute("role") == "listitem":
        data_pram_str = child_item.get_dom_attribute("data-params")
        if data_pram_str:
            #This is a question, turn it into a `Question`
            data_pram_json = json.loads('['+data_pram_str[4:])
            question_name = data_pram_json[0][1]
            question_type = data_pram_json[0][3]
            question_required = data_pram_json[0][4][0][2]
            question_point_value = 0
            points_element = try_find_element(web_element, XPATH_LISTITEM_POINTVALUE)
            if points_element:
                #This assignment is worth somthing, set the variable.
                point_regex = re.search(r"(.*) point", points_element.text)
                if point_regex:
                    question_point_value = int(point_regex.group(1))
            
            question = None
            if question_type == 0: # Short Str
                question = ShortTextQuestion(question_name, question_required, question_point_value)
            
            elif question_type == 1: # Long Str
                question = LongTextQuestion(question_name, question_required, question_point_value)
            
            elif question_type == 2:
                awnsers = [values[0] for values in data_pram_json[0][4][0][1]]
                question = MultipleChoiceQuestion(question_name, question_required, question_point_value, awnsers)
            
            elif question_type == 4:
                awnsers = [values[0] for values in data_pram_json[0][4][0][1]]
                question = MultipleChoiceQuestion(question_name, question_required, question_point_value, awnsers)
            
            else: raise NotImplemented(f"Question Type {question_type}")

            section.questions.append(question)
        elif child_item.get_dom_attribute("role") == "heading":
            # This is a section header
            # Update the section name
            section.name = child_item.find_element(By.XPATH, "div/div").text
    elif child_item != None and child_item.get_dom_attribute("data-user-email-address") != None:
        print("Email Checkbox")
    else:
        print("Not a Question, don't know what it could be")

def first_time_scan(web_driver: webdriver.Firefox) -> Form:
    form = Form()
    while True: #TODO: add logic to prevent trying to add the form results as an section
        section_element = find_list(web_driver)
        section = Section("Root")
        for child_element in section_element.find_elements(By.XPATH, '*'):
            scan_listitem(child_element, section)
        form.sections.append(section)
        form.print_form()
        fillout_section(web_driver, section)

a = make_webdriver()
a.get("https://docs.google.com/forms/d/e/1FAIpQLSdARHYqO539l9aJFIHYicuiLyH4SRCHckTwcjGnVqBvO_tYjg/formResponse")
input("> ")
first_time_scan(a)
input("> ")
a.close()