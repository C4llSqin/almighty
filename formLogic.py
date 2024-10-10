from abc import ABC
from hashlib import sha1
from os import path, mkdir
from itertools import chain
import io

def to_byte(num: int, length: int, cap: bool = False):
    max_for_len: int = (2 ** (length * 8)) - 1
    if   num > max_for_len and not cap: raise ValueError
    elif num > max_for_len and cap: return max_for_len.to_bytes(length, 'little', signed=False)
    else: return num.to_bytes(length, 'little', signed=False)

from_byte = lambda x: int.from_bytes(x, 'little', signed=False)

def read_str(buffer: io.BytesIO) -> str:
    buff = buffer.read(1)
    while not buff.endswith(b'\x00'): buff += buffer.read(1)
    return buff[:-1].decode()

COLOR_FORE_RED = "\033[31m"
COLOR_FORE_GREEN = "\033[32m"
COLOR_FORE_PINK = "\033[35m"
COLOR_FORE_CYAN = "\033[36m"
COLOR_FORE_YELLOW = "\033[93m"
RESET = "\033[0m"

class Awnser:
    MANUAL = 0
    CORRECT = 1
    UNKNOWN = 2
    INCORRECT = 3
    
    def __init__(self, name: str, status: int = UNKNOWN) -> None:
        self.name = name
        self.status = status
    
    def get_hashable_text(self) -> str:
        return self.name
    
    def export(self, buffer: io.BytesIO):
        buffer.write(
            self.name.encode() + b'\x00' +
            to_byte(self.status, 1)
        )
    
    def copy(self) -> "Awnser":
        return Awnser(self.name, self.status)

class Question(ABC):
    SCAN_FOR_AWNSER = 0
    MANUAL_MODE = 1
    NOTHING = 2
    AWAIT_INTERVENTION = 3

    QTYPE_MAP = {
        "Short Str": 0,
        "Long Str": 1,
        "multi": 2,
        "checkbox": 4
    }

    qtype = "unknown"

    def __init__(self, name: str, required: bool, points: int) -> None:
        self.name = name
        self.required = required
        self.points = points
        self.score_method = self.SCAN_FOR_AWNSER
        self.manual_awnser = None
        self.intervention_reason = "Unknown"
        if       required and not points: self.intervene("This question is ungraded, we need manual input")
        elif not required and not points: self.intervene("This question is ungraded and not reuired, we want manual input")
        elif not required and     points: self.intervene("This question is graded yet its not reuired, we want manual input")

    def print_question(self):
        print(f"{COLOR_FORE_CYAN}{self.name}{RESET} " + 
              ((COLOR_FORE_RED+"(REQ) "+RESET) * self.required) + 
              f"{COLOR_FORE_PINK}{self.points} pt(s){RESET} (qtype: {self.qtype})")

    def get_awnser(self) -> list[Awnser] | str:
        if self.score_method == Question.AWAIT_INTERVENTION:
            self.do_intervention()
        
        if self.score_method == Question.NOTHING: return []

        elif self.score_method == Question.MANUAL_MODE: return self.manual_awnser # type: ignore

        else: return self.scan_for_awnser()
    
    def do_intervention(self):
        print(f"\nIntervention Requested: {self.intervention_reason}")
        self.print_question()
        self.process_intervention()

    def process_intervention(self):
        text_in = input(f"{self.qtype}> ")
        raise NotImplemented

    def scan_for_awnser(self) -> list[Awnser]:
        raise NotImplemented

    def _prompt_user(self) -> str:
        return input(f"{self.qtype}> ")
    
    def intervene(self, reason: str):
        self.score_method = Question.AWAIT_INTERVENTION
        self.intervention_reason = reason
    
    def get_hashable_text(self) -> str:
        return f"{self.name}[{self.qtype}]"
    
    def export(self, buffer: io.BytesIO):
        buffer.write(
            self.name.encode() + b'\x00' +
            to_byte(self.points, 1, cap=True) +
            to_byte(int(self.required), 1) +
            to_byte(Question.QTYPE_MAP[self.qtype], 1)
        )

    def copy(self) -> "Question":
        raise NotImplementedError

class ShortTextQuestion(Question):
    qtype = "Short Str"

    def __init__(self, name: str, required: bool, points: int) -> None:
        super().__init__(name, required, points)
        self.manual_awnser = ""
        self.intervene("We don't correctly awnser text questions, please write the awnser.")
    
    def process_intervention(self):
        self.score_method = Question.MANUAL_MODE
        while True:
            text_in = input(f"{self.qtype}> ")
            if text_in and self.required: 
                self.manual_awnser = text_in
                break
            else: print("Required Question, Can't be empty")
    
    def export(self, buffer: io.BytesIO):
        super().export(buffer)
        buffer.write(self.manual_awnser.encode() + b'\x00')
    
    def copy(self) -> Question:
        question = type(self)(self.name, self.required, self.points)
        question.score_method = self.score_method
        question.manual_awnser = "".join([self.manual_awnser])
        question.intervention_reason = self.intervention_reason
        return question

class LongTextQuestion(ShortTextQuestion):
    qtype = "Long Str"

class MultipleChoiceQuestion(Question):
    qtype = "multi"

    def __init__(self, name: str, required: bool, points: int, awnsers: list[str]) -> None:
        super().__init__(name, required, points)
        self.awnsers = [Awnser(awnser) for awnser in awnsers]
    
    def print_question(self):
        super().print_question()
        i = 0
        for awnser in self.awnsers:
            print(f"{hex(i)[2:]}: ", end='')
            if   awnser.status == Awnser.MANUAL: print(COLOR_FORE_YELLOW, end='')
            elif awnser.status == Awnser.CORRECT: print(COLOR_FORE_GREEN, end='')
            elif awnser.status == Awnser.UNKNOWN: print(COLOR_FORE_PINK, end='')
            else: print(COLOR_FORE_RED, end='')
            print(f"{awnser.name}{RESET}")
            i+=1

    def is_manual(self):
        return self.score_method == self.MANUAL_MODE

    def scan_for_awnser(self) -> list[Awnser]:
        results = sorted(self.awnsers, key=lambda awnser: awnser.status)
        return [results[0]] # return either the correct awnser, an unknown awnser, or a human manual awnser(usually period id).
    
    def process_intervention(self):
        scan_available = self.points > 0
        none_available = not self.required
        if scan_available: print(f"{COLOR_FORE_GREEN}SCAN: AVAILABLE{RESET}")
        else: print(f"{COLOR_FORE_RED}SCAN: UNAVAILABLE{RESET}")
        if none_available: print(f"{COLOR_FORE_GREEN}NONE: AVAILABLE{RESET}")
        else: print(f"{COLOR_FORE_RED}NONE: UNAVAILABLE{RESET}")
        while True:
            try:
                val = input(f"{self.qtype}> ")
                if (val == "" or val == "@" or val.lower() == "auto"):
                    if scan_available:
                        self.score_method = Question.SCAN_FOR_AWNSER
                        return
                    else: raise ValueError
                if (val == "#" or val.lower() == "none"):
                    if none_available: 
                        self.score_method = Question.NOTHING
                        return
                    else: raise ValueError
                self.manual_input_parse(val)
                return
            except ValueError:
                print("Response Invalid, Try again.")

    def manual_input_parse(self, text: str):
        num = int(text, base=16)
        self.score_method = Question.MANUAL_MODE
        self.awnsers[num].status = Awnser.MANUAL
        self.manual_awnser = [self.awnsers[num]]

    def find_awnser(self, name: str) -> Awnser | None:
        for awnser in self.awnsers:
            if awnser.name == name: return awnser
        return None

    def get_hashable_text(self) -> str:
        return super().get_hashable_text() + f"({','.join([awnser.get_hashable_text() for awnser in sorted(self.awnsers, key=lambda x: x.name)])})"

    def export(self, buffer: io.BytesIO):
        super().export(buffer)
        buffer.write(to_byte(len(self.awnsers), 1))
        for awnser in self.awnsers:
            awnser.export(buffer)

    def copy(self) -> Question:
        question = type(self)(self.name, self.required, self.points, [])
        question.score_method = self.score_method
        question.awnsers = [awnser.copy() for awnser in self.awnsers]
        
        question.intervention_reason = self.intervention_reason
        if self.manual_awnser == None:
            question.manual_awnser = None
        else:
            indexes = [self.manual_awnser.index(awnser) for awnser in self.awnsers]
            question.manual_awnser = [question.awnsers[index] for index in indexes]
        return question
    
class CheckboxQuestion(MultipleChoiceQuestion):
    qtype = "checkbox"
    
    def __init__(self, name: str, required: bool, points: int, awnsers: list[str]) -> None:
        super().__init__(name, required, points, awnsers)
        self.choice_feedback = True

    def scan_for_awnser(self) -> list[Awnser]:
        return [awnser for awnser in self.awnsers if awnser.status < Awnser.INCORRECT] # return either the correct awnser, an unknown awnser, or a human manual awnser(usually period id).

    def process_intervention(self):
        scan_available = self.points > 0 and self.choice_feedback
        none_available = not self.required
        if scan_available: print(f"{COLOR_FORE_GREEN}SCAN: AVAILABLE{RESET}")
        else: print(f"{COLOR_FORE_RED}SCAN: UNAVAILABLE{RESET}")
        if none_available: print(f"{COLOR_FORE_GREEN}NONE: AVAILABLE{RESET}")
        else: print(f"{COLOR_FORE_RED}NONE: UNAVAILABLE{RESET}")
        while True:
            try:
                val = input(f"{self.qtype}> ")
                if (val == "" or val == "@" or val.lower() == "auto"):
                    if scan_available:
                        self.score_method = Question.SCAN_FOR_AWNSER
                        return
                    else: raise ValueError
                if (val == "#" or val.lower() == "none"):
                    if none_available: 
                        self.score_method = Question.NOTHING
                        return
                    else: raise ValueError
                self.manual_input_parse(val)
                return
            except ValueError:
                print("Response Invalid, Try again.")

    def manual_input_parse(self, text: str):
        try: 
            selected = [self.awnsers[int(va, base=16)] for va in text.split(';')]
            self.score_method = Question.MANUAL_MODE
            self.manual_awnser = selected
            for sel in selected: sel.status = Awnser.MANUAL
        except: raise ValueError
    
    def copy(self) -> Question:
        question = super().copy()
        assert isinstance(question, type(self))
        question.choice_feedback = self.choice_feedback
        return question

class Section():
    def __init__(self, name: str, questions: list[Question] = None) -> None: # type: ignore
        self.name = name
        if questions == None: questions = []
        self.questions: list[Question] = questions
    
    def search_by_question_title(self, name: str) -> Question | None:
        for question in self.questions:
            if question.name.startswith(name.strip()): return question
        return None
    
    def print_section(self):
        print(f"{COLOR_FORE_CYAN}## Section: {self.name} ##{RESET}")
        print()
        for question in self.questions:
            question.print_question()
            print()
        print(f"{COLOR_FORE_CYAN}####{RESET}")
    
    def get_hashable_text(self) -> str:
        return f"{self.name}({','.join([question.get_hashable_text() for question in sorted(self.questions, key=lambda x: x.name)])})"
    
    def export(self, buffer: io.BytesIO):
        buffer.write(self.name.encode() + b'\x00')
        buffer.write(to_byte(len(self.questions), 1))
        for question in self.questions:
            question.export(buffer)
    
    @staticmethod
    def from_file(buffer: io.BytesIO):
        name = read_str(buffer)
        questions = []
        for _ in range(from_byte(buffer.read(1))):
            question_name = read_str(buffer)
            points = from_byte(buffer.read(1))
            requred = bool(from_byte(buffer.read(1)))
            qtype = from_byte(buffer.read(1))

            if qtype == 0 or qtype == 1:
                awnser = read_str(buffer)
                
                if qtype == 0: question = ShortTextQuestion(question_name, requred, points)
                else: question = LongTextQuestion(question_name, requred, points)

                if not awnser: 
                    question.intervene("`.form` didn't provide an awnser for this one.")
                else:
                    question.score_method = Question.MANUAL_MODE
                    question.manual_awnser = awnser
                
            if qtype == 2 or qtype == 4:
                awnsers = [Awnser(read_str(buffer), from_byte(buffer.read(1))) for _ in range(from_byte(buffer.read(1)))]
                if qtype == 2: question = MultipleChoiceQuestion(question_name, requred, points, [])
                else: question = CheckboxQuestion(question_name, requred, points, [])

                question.awnsers = awnsers
            
            questions.append(question)
        return Section(name, questions)
    
    def copy(self) -> "Section":
        questions = [question.copy() for question in self.questions]
        return Section(self.name, questions)

class Form():
    def __init__(self, sections: list[Section] = None) -> None: # type: ignore
        if sections == None: sections = []
        self.sections: list[Section] = sections
    
    def search_by_question_title(self, name: str) -> Section | None:
        for section in self.sections:
            if section.name == name: return section
        return None

    def print_form(self):
        print(f"{COLOR_FORE_YELLOW}#### Form ####{RESET}")
        print()
        for section in self.sections:
            section.print_section()
        print(f"{COLOR_FORE_YELLOW}########{RESET}")
    
    def get_hashable_text(self) -> str:
        return ",".join([section.get_hashable_text() for section in self.sections])
    
    def export(self, buffer: io.BytesIO):
        buffer.write(to_byte(len(self.sections), 1))
        for section in self.sections: section.export(buffer)

    @staticmethod
    def from_file(buffer: io.BytesIO):
        sections = [Section.from_file(buffer) for _ in range(from_byte(buffer.read(1)))]
        return Form(sections)

    def copy(self) -> "Form":
        sections = [section.copy() for section in self.sections]
        return Form(sections)


def strip_info(question: Question):
    if isinstance(question, ShortTextQuestion):
        question.manual_awnser = ""
    else:
        assert isinstance(question, MultipleChoiceQuestion)
        for awnser in question.awnsers: awnser.status = Awnser.UNKNOWN

def strip_form(form: Form, mode: str):
    if mode != "all":
        questions: list[Question] = []
        for section in form.sections: questions.extend(section.questions)

        for question in questions:
            if mode == "empty": strip_info(question)
            elif not question.points and mode == "scored": strip_info(question)

def export(form: Form, mode: str, directory: str, reason: str):
    if mode == "ask":
        while mode not in ["all", "scored", "none", "empty"]: 
            mode = input(f"export mode [all, scored, ask, none, empty]({reason=})> ").lower()
            if mode == "ask": 
                print("What do you think we're doing now?")
                continue
            if mode in ["all", "scored", "none", "empty"]: 
                break
            print("Invalid input")

    if mode == "none": return

    if not path.exists(directory): mkdir(directory)
    form = form.copy()
    strip_form(form, mode)

    text_hash = sha1(form.get_hashable_text().encode()).hexdigest()
    with open(f"{directory}{text_hash}.form", 'wb') as f:
        form.export(f) # type: ignore

def import_from_file(fp: str) -> Form:
    with open(fp, 'rb') as f:
        return Form.from_file(f) # type: ignore

def combine_form(form_new: Form, form_old: Form):
    # Note: this mutates the new form. 
    new_questions: list[list[Question]] = []
    for section in form_new.sections: new_questions.append(section.questions)

    old_questions: list[list[Question]] = []
    for i in range(len(new_questions)):
        old_questions.append([])
        for new_question in new_questions[i]:
            
            old_question = form_old.sections[i].search_by_question_title(new_question.name)
            assert old_question != None, "Forms are not the same."
            old_questions[i].append(old_question)
    
    new_questions_flat = list(chain(*new_questions))
    old_questions_flat = list(chain(*old_questions))
    
    for i in range(len(new_questions_flat)):
        new_question = new_questions_flat[i]
        old_question = old_questions_flat[i]
        assert type(new_question) == type(old_question), "Forms are not the same."
    
        if isinstance(new_question, MultipleChoiceQuestion):
            assert isinstance(old_question, MultipleChoiceQuestion), "Forms are not the same."
            for awnser_a, awnser_b in zip(new_question.awnsers, old_question.awnsers):
                if awnser_a.status != Awnser.UNKNOWN: pass
                elif awnser_b.status != Awnser.UNKNOWN: awnser_a.status = awnser_b.status
        
        if isinstance(new_question, ShortTextQuestion):
            assert isinstance(old_question, ShortTextQuestion), "Forms are not the same."
            new_question.score_method = Question.MANUAL_MODE
            if new_question.manual_awnser != "": pass
            elif old_question.manual_awnser != "": new_question.manual_awnser = old_question.manual_awnser
            
            if new_question.manual_awnser == "": new_question.intervene(".form didn't provide an awnser for this one")

hash_form = lambda form: sha1(form.get_hashable_text().encode()).hexdigest()