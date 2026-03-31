import random
import string
import tkinter as tk
from tkinter import messagebox, simpledialog

def generate_password(length):
    chars = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(chars) for _ in range(length))
    return password

def main():
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    root.title("Генератор паролей")
    
    while True:
        user_input = simpledialog.askstring(
            "Генератор паролей", 
            "Введи длину пароля (минимум 6):\n(Отмена для выхода)"
        )
        
        if user_input is None:  # Нажали Отмена
            break
        
        try:
            length = int(user_input)
            if length < 6:
                messagebox.showwarning("Внимание", "Слишком коротко! Минимум 6 символов.")
                continue
            
            password = generate_password(length)
            messagebox.showinfo("Твой пароль", password)
            
            # Копируем в буфер обмена
            root.clipboard_clear()
            root.clipboard_append(password)
            messagebox.showinfo("Удобно", "Пароль скопирован в буфер обмена!")
            
        except ValueError:
            messagebox.showerror("Ошибка", "Нужно ввести число!")
    
    root.destroy()

if __name__ == "__main__":
    main()
