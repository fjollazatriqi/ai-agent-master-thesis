def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b != 0:
        return a / b
    else:
        return "Cannot divide by zero"

def modulus(a, b):
    return a % b

def exponentiate(base, exp):
    return base ** exp

def floor_divide(a, b):
    if b != 0:
        return a // b
    else:
        return "Cannot divide by zero"