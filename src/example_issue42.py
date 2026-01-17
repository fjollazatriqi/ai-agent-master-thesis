def add(a, b):
    """
    Adds two numbers.

    Parameters:
    a (int, float): The first number.
    b (int, float): The second number.

    Returns:
    int, float: The sum of a and b.
    """
    return a + b

def subtract(a, b):
    """
    Subtracts the second number from the first.

    Parameters:
    a (int, float): The first number.
    b (int, float): The second number.

    Returns:
    int, float: The difference of a and b.
    """
    return a - b

def multiply(a, b):
    """
    Multiplies two numbers.

    Parameters:
    a (int, float): The first number.
    b (int, float): The second number.

    Returns:
    int, float: The product of a and b.
    """
    return a * b

def divide(a, b):
    """
    Divides the first number by the second.

    Parameters:
    a (int, float): The numerator.
    b (int, float): The denominator.

    Returns:
    float: The quotient of a and b.

    Raises:
    ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

def power(base, exponent):
    """
    Raises a number to the power of another.

    Parameters:
    base (int, float): The base number.
    exponent (int, float): The exponent.

    Returns:
    int, float: The result of base raised to the power of exponent.
    """
    return base ** exponent

def square_root(x):
    """
    Calculates the square root of a number.

    Parameters:
    x (int, float): The number.

    Returns:
    float: The square root of x.

    Raises:
    ValueError: If x is negative.
    """
    if x < 0:
        raise ValueError("Cannot calculate the square root of a negative number.")
    return x ** 0.5