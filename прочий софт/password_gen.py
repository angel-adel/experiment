import random
import string

def generate_password(length):
    # Берем все возможные символы: буквы, цифры, знаки препинания
    chars = string.ascii_letters + string.digits + string.punctuation
    
    # Генерируем пароль случайным выбором
    password = ''.join(random.choice(chars) for _ in range(length))
    return password

def main():
    print("Привет, Дима! Давай создадим надежный пароль.")
    
    while True:
        try:
            user_input = input("\nВведи желаемую длину пароля (или 'q' для выхода): ")
            
            if user_input.lower() == 'q':
                print("Бывай, творец! До связи.")
                break
            
            length = int(user_input)
            
            if length < 6:
                print("Слишком коротко, давай хотя бы 6 символов для надежности.")
                continue
            
            password = generate_password(length)
            print(f"🔐 Твой пароль: {password}")
            
            # Можно сразу скопировать, если нужно, но пока просто выводим
            
        except ValueError:
            print("Эй, нужно ввести число! Попробуй еще раз.")

if __name__ == "__main__":
    main()
