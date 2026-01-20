def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

def power(base, exponent):
    return base ** exponent

def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def square_root(n):
    if n < 0:
        raise ValueError("Cannot take the square root of a negative number.")
    return n ** 0.5

def modulus(a, b):
    return a % b

def average(numbers):
    if not numbers:
        raise ValueError("The list is empty.")
    return sum(numbers) / len(numbers)

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

def power(base, exponent):
    return base ** exponent

def modulus(a, b):
    return a % b

def square_root(x):
    if x < 0:
        raise ValueError("Cannot take the square root of a negative number.")
    return x ** 0.5

def average(numbers):
    return sum(numbers) / len(numbers) if numbers else 0

def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

def power(base, exponent):
    return base ** exponent

def square_root(x):
    if x < 0:
        raise ValueError("Cannot take square root of a negative number.")
    return x ** 0.5

def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result