def group_even_odd(numbers):
    even = []
    odd = []
    for number in numbers:
        if number % 2 == 0:
            even.append(number)
        else:
            odd.append(number)
    return even, odd

# Example usage:
# even_numbers, odd_numbers = group_even_odd([1, 2, 3, 4, 5, 6])