from abc import ABC

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

class Question(ABC):
    SCAN_FOR_AWNSER = 0
    MANUAL_MODE = 1
    NOTHING = 2
    AWAIT_INTERVENTION = 3

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

class ShortTextQuestion(Question):
    qtype = "Short Str"

    def __init__(self, name: str, required: bool, points: int) -> None:
        super().__init__(name, required, points)
        self.intervene("We don't correctly awnser text questions, please write the awnser.")
    
    def process_intervention(self):
        self.score_method = Question.MANUAL_MODE
        while True:
            text_in = input(f"{self.qtype}> ")
            if text_in and self.required: 
                self.manual_awnser = text_in
                break
            else: print("Required Question, Can't be empty")

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

    def find_awnser(self, name: str) -> Awnser | None:
        for awnser in self.awnsers:
            if awnser.name == name: return awnser
        return None

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
        