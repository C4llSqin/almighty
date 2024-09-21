from selenium import webdriver
from selenium.webdriver.remote import webelement
from selenium.webdriver.common.by import By

from lxml import html

def to_webelement(web_driver: webdriver.Firefox, elm: html.Element) -> webelement.WebElement:
    xpath = "/html/" + elm.getroottree().getelementpath(elm)
    return web_driver.find_element(By.XPATH, xpath)

def variable_xpath(elm: html.Element, path: str, conditional = lambda elm: True):
    if "[var]/" not in path: 
        res_elm = elm.xpath(path)
        if len(res_elm) == 0: raise ValueError
        if conditional(res_elm): return res_elm
        raise ValueError
    segments = path.split("[var]/")
    parents = elm.xpath(segments[0])
    for parent in parents:
        try: return variable_xpath(parent, segments[1], conditional=conditional)
        except ValueError: pass
    raise ValueError

class wraped_element():
    def __init__(self, web_driver: webdriver.Firefox, elem: html.Element) -> None:
        self.web_driver = web_driver
        self.internal_element = elem
        assert not isinstance(elem, wraped_element)
        self.external_element = None
    
    def _get_text(self):
        return self.internal_element.text
    
    text = property(fget=_get_text)

    def get_dom_attribute(self, name: str) -> str:
        try: return self.internal_element.attrib[name]
        except: return ""

    def find_elements(self, _, path: str, conditional = None) -> list["wraped_element"]:
        found_elements = None
        if conditional == None: found_elements = variable_xpath(self.internal_element, path)
        else: found_elements = variable_xpath(self.internal_element, path, conditional=conditional)
        return [wraped_element(self.web_driver, element) for element in found_elements]

    def find_element(self, _, path: str, conditional = None) -> "wraped_element":
        return self.find_elements(_, path, conditional=conditional)[0]

    def to_real(self) -> webelement.WebElement:
        self.external_element = to_webelement(self.web_driver, self.internal_element)
        return self.external_element
    
    def click(self):
        if self.external_element == None: self.to_real()
        self.external_element.click() # type: ignore
    
    def clear(self):
        if self.external_element == None: self.to_real()
        self.external_element.clear() # type: ignore
    
    def send_keys(self, text: str):
        if self.external_element == None: self.to_real()
        self.external_element.send_keys(text) # type: ignore
