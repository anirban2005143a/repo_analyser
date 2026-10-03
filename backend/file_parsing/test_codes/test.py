# ==========================================
# 1. BASIC VARIABLES
# ==========================================

name = "Rahul"
age = 25
salary = 50000.0
is_employee = True

skills = ["Python", "SQL", "Git"]

print(name)
print(age)
print(salary)
print(is_employee)


# ==========================================
# 2. CONDITIONS
# ==========================================

if age >= 18:
    print("Adult")
elif age > 0:
    print("Minor")
else:
    print("Invalid age")


# ==========================================
# 3. FOR LOOP
# ==========================================

for skill in skills:
    print("Skill:", skill)


# ==========================================
# 4. WHILE LOOP
# ==========================================

counter = 1

while counter <= 5:
    print("Counter:", counter)
    counter += 1


# ==========================================
# 5. FUNCTION
# ==========================================


def greet(name):
    return f"Hello, {name}!"


message = greet("Rahul")
print(message)


# ==========================================
# 6. FUNCTION WITH DEFAULT ARGUMENT
# ==========================================


def calculate_salary(basic, bonus=5000):
    return basic + bonus


print(calculate_salary(40000))
print(calculate_salary(40000, 10000))


# ==========================================
# 7. *ARGS
# ==========================================


def add_numbers(*numbers):
    return sum(numbers)


print(add_numbers(10, 20))
print(add_numbers(10, 20, 30, 40))


# ==========================================
# 8. **KWARGS
# ==========================================


def show_details(**details):

    for key, value in details.items():
        print(key, ":", value)


show_details(name="Rahul", age=25, department="IT")


# ==========================================
# 9. CLASS
# ==========================================


class Employee:

    company = "ABC Technologies"

    def __init__(self, name, age, salary):
        self.name = name
        self.age = age
        self.salary = salary

    def introduce(self):
        print(f"My name is {self.name}. " f"I am {self.age} years old.")

    def annual_salary(self):
        return self.salary * 12


# Create object
emp = Employee("Rahul", 25, 50000)

emp.introduce()

print("Annual salary:", emp.annual_salary())


# ==========================================
# 10. INHERITANCE
# ==========================================


class Manager(Employee):

    def manage_team(self):
        print(self.name, "is managing the team.")


manager = Manager("Amit", 35, 80000)

manager.introduce()
manager.manage_team()


# ==========================================
# 11. DECORATOR
# ==========================================


def my_decorator(function):

    def wrapper():
        print("Before function")

        function()

        print("After function")

    return wrapper


@my_decorator
def say_hello():

    print("Hello!")


say_hello()


# ==========================================
# 12. DECORATOR WITH ARGUMENTS
# ==========================================


def log_function(function):

    def wrapper(*args, **kwargs):

        print("Function started")

        print("Arguments:", args)
        print("Keyword arguments:", kwargs)

        result = function(*args, **kwargs)

        print("Function finished")

        return result

    return wrapper


@log_function
def add(a, b):

    return a + b


result = add(10, 20)

print("Result:", result)


# ==========================================
# 13. DECORATOR WITH functools.wraps
# ==========================================

from functools import wraps


def logger(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        print(f"Calling function: {function.__name__}")

        result = function(*args, **kwargs)

        print("Function completed")

        return result

    return wrapper


@logger
def multiply(a, b):
    """Multiply two numbers."""

    return a * b


print(multiply(5, 10))

print("Function name:", multiply.__name__)
print("Documentation:", multiply.__doc__)


# ==========================================
# 14. DECORATOR FOR AUTHORIZATION
# ==========================================


def require_admin(function):

    @wraps(function)
    def wrapper(user, *args, **kwargs):

        if user.get("role") != "admin":
            print("Access denied!")

            return None

        return function(user, *args, **kwargs)

    return wrapper


@require_admin
def delete_user(user, username):

    print(f"{username} has been deleted.")


admin_user = {"name": "Rahul", "role": "admin"}

normal_user = {"name": "Amit", "role": "user"}


delete_user(admin_user, "John")

delete_user(normal_user, "John")


# ==========================================
# 15. DECORATOR FOR TIMING
# ==========================================

import time


def timer(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        start = time.time()

        result = function(*args, **kwargs)

        end = time.time()

        print(f"{function.__name__} " f"took {end - start:.4f} seconds")

        return result

    return wrapper


@timer
def slow_function():

    time.sleep(1)

    return "Done"


print(slow_function())


# ==========================================
# 16. STATIC METHOD
# ==========================================


class Calculator:

    @staticmethod
    def add(a, b):

        return a + b

    @staticmethod
    def multiply(a, b):

        return a * b


print(Calculator.add(10, 20))

print(Calculator.multiply(5, 10))


# ==========================================
# 17. CLASS METHOD
# ==========================================


class Employee:

    company = "ABC Technologies"

    def __init__(self, name, salary):

        self.name = name
        self.salary = salary

    @classmethod
    def change_company(cls, new_company):

        cls.company = new_company


print(Employee.company)

Employee.change_company("XYZ Technologies")

print(Employee.company)


# ==========================================
# 18. PROPERTY
# ==========================================


class Person:

    def __init__(self, name):

        self._name = name

    @property
    def name(self):

        return self._name

    @name.setter
    def name(self, value):

        if not value:
            raise ValueError("Name cannot be empty")

        self._name = value


person = Person("Rahul")

print(person.name)

person.name = "Amit"

print(person.name)


# ==========================================
# 19. LIST COMPREHENSION
# ==========================================

numbers = [1, 2, 3, 4, 5]

squares = [number**2 for number in numbers]

print(squares)


# ==========================================
# 20. DICTIONARY COMPREHENSION
# ==========================================

numbers = [1, 2, 3, 4, 5]

square_dict = {number: number**2 for number in numbers}

print(square_dict)


# ==========================================
# 21. EXCEPTION HANDLING
# ==========================================

try:

    number = int(input("Enter a number: "))

    result = 100 / number

    print(result)

except ValueError:

    print("Invalid number")

except ZeroDivisionError:

    print("Cannot divide by zero")

finally:

    print("Finished")


# ==========================================
# 22. FILE HANDLING
# ==========================================

with open("employees.txt", "w") as file:

    file.write("Rahul\n")
    file.write("Amit\n")


with open("employees.txt", "r") as file:

    content = file.read()

print(content)


# ==========================================
# 23. LAMBDA
# ==========================================

square = lambda x: x * x

print(square(5))


# ==========================================
# 24. MAP
# ==========================================

numbers = [1, 2, 3, 4, 5]

doubled = list(map(lambda x: x * 2, numbers))

print(doubled)


# ==========================================
# 25. FILTER
# ==========================================

even_numbers = list(filter(lambda x: x % 2 == 0, numbers))

print(even_numbers)


# ==========================================
# 26. ENUMERATE
# ==========================================

skills = ["Python", "SQL", "Docker"]

for index, skill in enumerate(skills, start=1):

    print(index, skill)


# ==========================================
# 27. MAIN ENTRY POINT
# ==========================================


def main():

    print("Application started")

    employee = Employee("John", 60000)

    print(employee.name)
    print(employee.salary)


if __name__ == "__main__":

    main()
