from selenium import webdriver
from selenium.webdriver.common.by import By
from formLogic import *
from netnavigation import *
from lxml import html
import re
import json
import time
from tqdm import tqdm
from colorama import init as term_init

XPATH_LISTITEM_POINTVALUE = "div/div/div[1]/div[2]"
XPATH_LISTITEM_SHORT_STR_INPUT = "div/div/div[2]/div/div[1]/div/div[1]/input"
XPATH_LISTITEM_LONG_STR_INPUT = "div/div/div[2]/div/div[1]/div[2]/textarea"
XPATH_LISTITEM_EMAIL_CHECK = "div[1]/label/div"
XPATH_LISTITEM_MULTI = "div/div/div[2]/div/div/span/div"
XPATH_LISTITEM_CHECKBOX = "div/div/div[2]/div[1]/"

XPATH_ROOT_STATUS = "/html/body/div/div[var]/form/div[2]/div/div[3]/div[1]"
XPATH_STATUS_PROGRESS_TEXT = "div[2]/div[2]"
XPATH_BUTTON_BUTTON_TEXT = "span/span"

XPATH_VIEW_RESULTS = "/html/body/div[1]/div[2]/div[1]/div/div[var]/div/a"

XPATH_RESULTS_SCORE = "/html/body/div/div[2]/div[1]/div/div[1]/div/div[2]/div/div[2]/span"
XPATH_RESULTS_SECTIONS = "/html/body/div/div[2]"

name = r"""
 ______   ___                           __      __                
/\  _  \ /\_ \               __        /\ \    /\ \__             
\ \ \L\ \\//\ \     ___ ___ /\_\     __\ \ \___\ \ ,_\  __  __    
 \ \  __ \ \ \ \  /' __` __`\/\ \  /'_ `\ \  _ `\ \ \/ /\ \/\ \   
  \ \ \/\ \ \_\ \_/\ \/\ \/\ \ \ \/\ \L\ \ \ \ \ \ \ \_\ \ \_\ \  
   \ \_\ \_\/\____\ \_\ \_\ \_\ \_\ \____ \ \_\ \_\ \__\\/`____ \ 
    \/_/\/_/\/____/\/_/\/_/\/_/\/_/\/___L\ \/_/\/_/\/__/ `/___/> \
                                     /\____/                /\___/
                                     \_/__/                 \/__/ 
"""[1:-1]

rgb_to_escape = lambda color: f"\033[38;2;{int(color[0])};{int(color[1])};{int(color[2])}m"

def display_logo():
    top_color = (0, 255, 0)
    bottom_color = (0, 255, 255)
    name_parts = name.split('\n')
    delta = (
        (bottom_color[0]-top_color[0])/(len(name_parts)-1), 
        (bottom_color[1]-top_color[1])/(len(name_parts)-1), 
        (bottom_color[2]-top_color[2])/(len(name_parts)-1)
    )
    current_color = top_color
    for line in name_parts:
        print(rgb_to_escape(current_color) + line)
        current_color = (
            current_color[0] + delta[0], 
            current_color[1] + delta[1], 
            current_color[2] + delta[2]
        )
    print("\033[0m", end="")

def gradent_str(text: str, color1: tuple[int, int, int], color2: tuple[int, int, int]):
    le = len(text) - 1 #short for length
    delta = (
        (color2[0]-color1[0])/le, 
        (color2[1]-color1[1])/le, 
        (color2[2]-color1[2])/le
    )
    current_color = color1
    new_str = ""
    for char in text:
        new_str += rgb_to_escape(current_color) + char
        current_color = (
            current_color[0] + delta[0], 
            current_color[1] + delta[1], 
            current_color[2] + delta[2]
        )

    return new_str + "\033[0m"


def make_webdriver() -> webdriver.Firefox:
    #TODO: make this read a json, and choose profiles.
    ffOptions = webdriver.FirefoxOptions()
    ffOptions.add_argument("-profile")
    with open("profilepath.txt") as f:
        ffOptions.add_argument(f.read())
    return webdriver.Firefox(ffOptions)

def try_find_element(web_element: wraped_element, xpath: str):
    try:
        return web_element.find_element(By.XPATH, xpath)
    except:
        return None

def make_root(web_driver: webdriver.Firefox) -> wraped_element:
    whole_html = web_driver.page_source # literaly the whole html as plain text
    tree = html.fromstring(whole_html)
    return wraped_element(web_driver, tree)

def find_list(web_driver: webdriver.Firefox) -> tuple[wraped_element, wraped_element]:
    whole_html = web_driver.page_source # literaly the whole html as plain text
    tree = html.fromstring(whole_html)
    root_elm = wraped_element(web_driver, tree)
    section_start = re.search(r"<div class=\"(.{3,6})\" role=\"list\">", whole_html)
    assert section_start != None
    section_start_class_name = section_start.group(1)
    elm = root_elm.find_element(By.XPATH, f"//div[@class='{section_start_class_name}']")
    return (elm, root_elm)

def fillout_section(section_element: wraped_element, section: Section):
    for listitem in tqdm(section_element.find_elements(By.XPATH, '*'), colour = '#e942f5', unit='question', desc = 'fillout_section', leave=False):
        child_item = listitem.find_element(By.XPATH, "div")
        if listitem.get_dom_attribute("role") == "listitem":
            data_pram_str = child_item.get_dom_attribute("data-params")
            if data_pram_str:
                #This is a question, get the `Question` from the `Section` and then get the awnser and apply the awnser.
                data_pram_json = json.loads('['+data_pram_str[4:])
                question_name = data_pram_json[0][1]
                question_type = data_pram_json[0][3]
            
                question = section.search_by_question_title(question_name)
                assert (question != None)
                awnser = question.get_awnser()
                
                if question_type == 0 or question_type == 1:
                    assert isinstance(awnser, str)
                    text_box = None
                    if question_type: text_box = listitem.find_element(By.XPATH, XPATH_LISTITEM_LONG_STR_INPUT)
                    else: text_box = listitem.find_element(By.XPATH, XPATH_LISTITEM_SHORT_STR_INPUT)
                    text_box.click()
                    text_box.clear()
                    text_box.send_keys(awnser)
                
                elif question_type == 2 or question_type == 4:
                    assert isinstance(awnser, list)
                    button_order = [values[0] for values in data_pram_json[0][4][0][1]]
                    for sub_awnser in awnser:
                        if sub_awnser.name in button_order:
                            i = button_order.index(sub_awnser.name)
                            if question_type == 2:
                                container = listitem.find_element(By.XPATH, XPATH_LISTITEM_MULTI)
                                clickable = wraped_element(container.web_driver, container.internal_element[i])
                                clickable.click()
                            if question_type == 4:
                                clickable = listitem.find_element(By.XPATH, f"{XPATH_LISTITEM_CHECKBOX}div[{1+i}]")
                                clickable.click()
                            
                time.sleep(0.1)
            
        elif child_item != None and child_item.get_dom_attribute("data-user-email-address") != None:
            #Email Checkbox, click on it
            #TODO: find the XPATH to the actual clickable area.
            clickable = listitem.find_element(By.XPATH, XPATH_LISTITEM_EMAIL_CHECK)
            clickable.click()
        else:
            print("Not a Question, don't know what it could be")

def fillout_form(web_driver: webdriver.Firefox, form: Form) -> tuple[tuple[int, int], wraped_element, wraped_element]:
    # webdriver.find_element(By.)
    i = 0
    bar = tqdm(total = len(form.sections), colour = '#ffff00', unit='section', desc = 'fillout_form', leave=False)
    while True:
        section = form.sections[i]
        section_element, root_tree = find_list(web_driver)
        fillout_section(section_element, section)
        progression = progress(root_tree)
        # print(progression[1])
        bar.update(n=1)
        if progression[0]: break
        i += 1
    root_tree = make_root(web_driver)
    link_elm = root_tree.find_element(By.XPATH, XPATH_VIEW_RESULTS)
    link = link_elm.get_dom_attribute("href")
    web_driver.get(link)
    section_element, root_tree = find_list(web_driver)
    #get the score
    score_elm = root_tree.find_element(By.XPATH, XPATH_RESULTS_SCORE)
    points = score_elm.text.split('/')
    return (int(points[0]), int(points[1])), section_element, root_tree

def machine_learning(root_tree: wraped_element, form: Form): 
    section_containers = root_tree.find_element(By.XPATH, XPATH_RESULTS_SECTIONS)
    section_index = 0
    for section_container in section_containers.find_elements(By.XPATH, '*'):
        
        
        for section_element in section_container.find_elements(By.XPATH, 'div/*'):
            
            if section_element.get_dom_attribute("role") != "list": continue # isn't a section
            section = form.sections[section_index]
            
            for listitem_elm in section_element.find_elements(By.XPATH, '*'):
                if listitem_elm.get_dom_attribute("role") != "listitem": continue #isn't a question
                
                
                if len(listitem_elm.internal_element) > 1: child = listitem_elm.find_element(By.XPATH, "div[2]")
                else: child = listitem_elm.find_element(By.XPATH, "div")
                if child.get_dom_attribute("role") == "heading": continue # Not a question we can learn from.
                
                title_element = child.find_element(By.XPATH, "div[1]")
                title_componets = title_element.find_elements(By.XPATH, '*')
                if len(title_componets) != 2: continue #Ungraded
                
                score_str = title_componets[1].text
                compoents = score_str.split('/')
                question_name_element = title_componets[0].find_element(By.XPATH, "div/div[2]/span[1]")
                if question_name_element.text != None: question_name = question_name_element.text
                else:
                    question_name = ""
                    for p_element in question_name_element.find_elements(By.XPATH, 'p'):
                        if p_element.text != None: question_name = question_name + p_element.text
                
                question = section.search_by_question_title(question_name) # type: ignore # by following the order of events down the program it will eventually be a check box question
                assert question != None
                
                if compoents[0] == compoents[1]:
                    if type(question) == MultipleChoiceQuestion:
                        question.get_awnser()[0].status = Awnser.CORRECT # type: ignore # Mark the multiple choice awnser correct.
                    
                    continue # Already got the maxium points for this one.

                if isinstance(question, (ShortTextQuestion, LongTextQuestion)):
                    question.intervene("The awnser you provided was incorrect.")
                    continue # https://www.youtube.com/watch?v=S-9-49rM8yM
                
                if question.score_method == Question.NOTHING:
                    question.intervene("Putting nothing in a graded question won't get you points")
                    continue # who knew putting nothing in a graded question is a bad idea.
                
                awnsers: list[Awnser] = question.get_awnser() #type: ignore

                if question.score_method == Question.MANUAL_MODE:
                    question.intervene("The awnser you provided was incorect.")
                    # https://www.youtube.com/watch?v=S-9-49rM8yM

                #TODO: properly read all awnsers in a multiple choice for possibly more info.
                if type(question) == MultipleChoiceQuestion:
                    awnsers[0].status = Awnser.INCORRECT
                    continue 
                
                assert isinstance(question, CheckboxQuestion)

                body_element = child.find_element(By.XPATH, "div[2]")

                feed_back = False # Search if we get checkbox feedback

                for awnser_container in body_element.find_elements(By.XPATH, '*'):
                    awnser_name = awnser_container.get_dom_attribute("data-value")
                    res_awnser = question.find_awnser(awnser_name)
                    
                    assert res_awnser != None
                    
                    try: correctness_elem = awnser_container.find_element(By.XPATH, "div/label/div[2]")
                    except: continue
                    
                    feed_back = True
                    res_awnser.status = Awnser.CORRECT
                    if correctness_elem.get_dom_attribute("aria-label") == "Incorrect": res_awnser.status = Awnser.INCORRECT
                
                if not feed_back:
                    question.intervene("There is no awnser feed back for this multiple choice, SCAN is unavailable.")
                    for awnser in question.awnsers: awnser.status = Awnser.UNKNOWN
                    question.choice_feedback = False
                
            
            section_index += 1
    
def scan_listitem(web_element: wraped_element, section: Section):
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
                question = CheckboxQuestion(question_name, question_required, question_point_value, awnsers)
            
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

def progress(root_tree: wraped_element) -> tuple[bool, tuple[int, int]]:
    parent = root_tree.find_element(By.XPATH, XPATH_ROOT_STATUS)
    progress_val = (0,0)
    if len(parent.find_elements(By.XPATH, '*')) == 3:
        progress_text_elm = parent.find_element(By.XPATH, XPATH_STATUS_PROGRESS_TEXT)
        match = re.search(r"Page (.*) of (.*)", progress_text_elm.text)
        assert match != None
        progress_val = (int(match.group(1)), int(match.group(2)))
        #We have a progress bar

    button_container = parent.find_element(By.XPATH, "div[1]")
    for button in button_container.find_elements(By.XPATH, '*'):
        button_text_elm = button.find_element(By.XPATH, XPATH_BUTTON_BUTTON_TEXT)
        if button_text_elm.text == "Submit":
            button.click()
            return (True, progress_val)
        elif button_text_elm.text == "Next":
            button.click()
            return (False, progress_val)
    raise ValueError("Unable to find the path for progression")

def first_time_scan(web_driver: webdriver.Firefox) -> tuple[Form, tuple[int, int], wraped_element]:
    form = Form()
    while True:
        section_element, root_tree = find_list(web_driver)
        section = Section("Root")
        for child_element in section_element.find_elements(By.XPATH, '*'):
            scan_listitem(child_element, section)
        form.sections.append(section)
        fillout_section(section_element, section)
        progression = progress(root_tree)
        # print(progression[1])
        if progression[0]: break
    # form.print_form()
    root_tree = make_root(web_driver)
    link_elm = root_tree.find_element(By.XPATH, XPATH_VIEW_RESULTS)
    link = link_elm.get_dom_attribute("href")
    web_driver.get(link)
    
    #get the score
    root_tree = make_root(web_driver)
    score_elm = web_driver.find_element(By.XPATH, XPATH_RESULTS_SCORE)
    points = score_elm.text.split('/')
    return form, (int(points[0]), int(points[1])), root_tree

def main():
    term_init()
    display_logo()
    url = input("formURL> ")
    print(f"\"{gradent_str('Gaze on my Works, ye Mighty, and despair!', (0,255,0), (0,255,255))}\"")
    web_driver = make_webdriver()
    main_loop(web_driver, url)

def main_loop(web_driver, url: str):
    web_driver.get(url)
    form, score, root_tree = first_time_scan(web_driver)
    score_bar = tqdm(total=score[1], desc='Score', unit='pt', colour='#00ff00')
    score_bar.update(n=score[0])
    while score[0] != score[1]:
        tstart = time.time()
        machine_learning(root_tree, form)
        tend = time.time()
        # print(f"Machine Learing took {round((tend-tstart)*1000, 2)}MS")
        web_driver.get(url)
        score, _, root_tree = fillout_form(web_driver, form)
        score_bar.update(n=score[0] - score_bar.n)
    form.print_form()
    web_driver.close()

if __name__ == "__main__":
    main()