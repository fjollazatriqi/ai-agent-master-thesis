from tkinter import Tk, Label, Entry, Button, StringVar, messagebox

def login():
    username = username_var.get()
    password = password_var.get()
    if username == "admin" and password == "password":
        messagebox.showinfo("Login", "Login successful!")
    else:
        messagebox.showerror("Login", "Invalid credentials")

root = Tk()
root.title("Login Form")

username_var = StringVar()
password_var = StringVar()

Label(root, text="Username").grid(row=0, column=0)
Entry(root, textvariable=username_var).grid(row=0, column=1)

Label(root, text="Password").grid(row=1, column=0)
Entry(root, textvariable=password_var, show='*').grid(row=1, column=1)

Button(root, text="Login", command=login).grid(row=2, columnspan=2)

root.mainloop()