document = open("aritmetika_shembuj.py", "w")

document.write("""
# Funksionet Aritmetike

# Shtimi
def shtimi(a, b):
    return a + b

# Zbritja
def zbritja(a, b):
    return a - b

# Shumzimi
def shumzimi(a, b):
    return a * b

# Pjesetimi
def pjesetimi(a, b):
    return a / b if b != 0 else 'Nuk mund te behet pjesetimi me zero'

# Shembuj te perdorimit
print("Shtimi: ", shtimi(5, 3))
print("Zbritja: ", zbritja(5, 3))
print("Shumzimi: ", shumzimi(5, 3))
print("Pjesetimi: ", pjesetimi(5, 3))
""")

document.close()