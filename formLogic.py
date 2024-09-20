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
    qtype = "unknown"

    def __init__(self, name: str, required: bool, points: int) -> None:
        self.name = name
        self.required = required
        self.points = points

    def print_question(self):
        print(f"{COLOR_FORE_CYAN}{self.name}{RESET} " + 
              ((COLOR_FORE_RED+"(REQ) "+RESET) * self.required) + 
              f"{COLOR_FORE_PINK}{self.points} pt(s){RESET} (qtype: {self.qtype})")

    def get_awnser(self) -> list[Awnser] | str:
        return "OHNO!"

    def _prompt_user(self) -> str:
        return input(f"{self.qtype}> ")

class ShortTextQuestion(Question):
    qtype = "Short Str"

    def __init__(self, name: str, required: bool, points: int) -> None:
        super().__init__(name, required, points)
        self.val = "##UNKNOWN##"

    def get_awnser(self) -> str:
        if self.val == "##UNKNOWN##":
            self.print_question()
            print(f"Unbruteable qtype: {self.qtype}")
            self.val = self._prompt_user()
        return self.val

class LongTextQuestion(ShortTextQuestion):
    qtype = "Long Str"

class MultipleChoiceQuestion(Question):
    qtype = "multi"

    def __init__(self, name: str, required: bool, points: int, awnsers: list[str]) -> None:
        super().__init__(name, required, points)
        self.awnsers = [Awnser(awnser) for awnser in awnsers]
        self.no_awnser = False
    
    def print_question(self):
        super().print_question()
        i = 0
        for awnser in self.awnsers:
            print(f"{hex(i)}: {awnser.name}")
            i+=1

    def has_manual(self):
        return any([awnser.status==Awnser.MANUAL for awnser in self.awnsers])

    def get_awnser(self):
        if self.no_awnser: return []

        input_req = False #input requested
        auto_available = True
        none_available = False
        if not self.required and all([awnser.status==Awnser.UNKNOWN for awnser in self.awnsers]):
            # if not required and first time, so none is available
            input_req = True
            none_available = True

        if self.points == 0 and all([awnser.status==Awnser.UNKNOWN for awnser in self.awnsers]):
            # if no points and no manual awnser selected, so auto isn't available
            input_req = True
            auto_available = False

        if input_req:
            self.print_question()
            print("Manual input requested")
            if auto_available: print(f"{COLOR_FORE_GREEN}AUTO: AVAILABLE{RESET}")
            else: print(f"{COLOR_FORE_RED}AUTO: UNAVAILABLE{RESET}")
            if none_available: print(f"{COLOR_FORE_GREEN}NONE: AVAILABLE{RESET}")
            else: print(f"{COLOR_FORE_RED}NONE: UNAVAILABLE{RESET}")
            while True:
                try:
                    val = self._prompt_user()
                    if (val == "" or val == "@" or val.lower() == "auto"):
                        if auto_available: break
                        else: raise ValueError
                    if (val == "#" or val.lower() == "none"):
                        if none_available: 
                            self.no_awnser=True
                            return []
                        else: raise ValueError
                    num = int(val, base=16)
                    self.awnsers[num].status = Awnser.MANUAL
                    return [self.awnsers[num]]
                except ValueError:
                    print("Response Invalid, Try again.")

        results = sorted(self.awnsers, key=lambda awnser: awnser.status)
        return [results[0]] # return either the correct awnser, an unknown awnser, or a human manual awnser(usually period id).
    
class CheckboxQuestion(MultipleChoiceQuestion):
    qtype = "checkbox"
    
    def get_awnser(self):
        if self.no_awnser: return []

        input_req = False #input requested
        auto_available = True
        none_available = False
        if not self.required and all([awnser.status==Awnser.UNKNOWN for awnser in self.awnsers]):
            # if not required and first time, so none is available
            input_req = True
            none_available = True

        if self.points == 0 and all([awnser.status==Awnser.UNKNOWN for awnser in self.awnsers]):
            # if no points and no manual awnser selected, so auto isn't available
            input_req = True
            auto_available = False

        if input_req:
            self.print_question()
            print("Manual input requested")
            if auto_available: print(f"{COLOR_FORE_GREEN}AUTO: AVAILABLE{RESET}")
            else: print(f"{COLOR_FORE_RED}AUTO: UNAVAILABLE{RESET}")
            if none_available: print(f"{COLOR_FORE_GREEN}NONE: AVAILABLE{RESET}")
            else: print(f"{COLOR_FORE_RED}NONE: UNAVAILABLE{RESET}")
            while True:
                try:
                    val = self._prompt_user()
                    if (val == "" or val == "@" or val.lower() == "auto"):
                        if auto_available: break
                        else: raise ValueError
                    if (val == "#" or val.lower() == "none"):
                        if none_available: 
                            self.no_awnser=True
                            return []
                        else: raise ValueError
                    
                    selected = [self.awnsers[int(va, base=16)] for va in val.split(';')]
                    for awnser in self.awnsers: awnser.status = Awnser.INCORRECT
                    for sel in selected: sel.status = Awnser.MANUAL
                    return selected
                except ValueError:
                    print("Response Invalid, Try again.")

        results = [awnser for awnser in self.awnsers if awnser.status < Awnser.INCORRECT]
        return results # return either the correct awnser, an unknown awnser, or a human manual awnser(usually period id).

class Section():
    def __init__(self, name: str, questions: list[Question] = None) -> None:
        self.name = name
        if questions == None: questions = []
        self.questions: list[Question] = questions
    
    def search_by_question_title(self, name: str) -> Question | None:
        for question in self.questions:
            if question.name == name: return question
        return None
    
    def print_section(self):
        print(f"{COLOR_FORE_CYAN}## Section: {self.name} ##{RESET}")
        print()
        for question in self.questions:
            question.print_question()
            print()
        print(f"{COLOR_FORE_CYAN}####{RESET}")

class Form():
    def __init__(self, sections: list[Section] = None) -> None:
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
        