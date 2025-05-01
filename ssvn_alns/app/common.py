tests = {1: 'first_day', 2: 'second_day', 3: 'third_day'}

class User:

    def __init__(self, name, birth_date, completed_tests_state):
        self.name = name
        self.birth_date = birth_date
        self.completed_tests_state = 0

user = User(0,0,0)