import time
import random
import sys
import os
from pathlib import Path

# ========== ЦВЕТА (как в прошлом коде) ==========
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def color_text(text, color):
    return f"{color}{text}{Colors.END}"

def highlight_differences(original: str, user: str) -> str:
    result = []
    max_len = max(len(original), len(user))
    for i in range(max_len):
        if i < len(original) and i < len(user):
            if original[i] == user[i]:
                result.append(color_text(user[i], Colors.GREEN))
            else:
                result.append(color_text(user[i], Colors.RED))
        elif i < len(user):
            result.append(color_text(user[i], Colors.RED))
        else:
            result.append(color_text('_', Colors.RED))
    return ''.join(result)

def calculate_errors(original: str, user: str) -> tuple:
    max_len = max(len(original), len(user))
    errors = 0
    for i in range(max_len):
        orig_char = original[i] if i < len(original) else ''
        user_char = user[i] if i < len(user) else ''
        if orig_char != user_char:
            errors += 1
    error_percent = (errors / len(original)) * 100 if len(original) > 0 else 0
    orig_words = original.split()
    user_words = user.split()
    correct_words = 0
    for i in range(min(len(orig_words), len(user_words))):
        if orig_words[i] == user_words[i]:
            correct_words += 1
    return errors, error_percent, correct_words

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_fancy_header(text: str):
    width = 60
    print(color_text("═" * width, Colors.CYAN))
    print(color_text(f"  {text.center(width-2)}", Colors.BOLD + Colors.YELLOW))
    print(color_text("═" * width, Colors.CYAN))

def print_colored_comparison(original: str, user: str):
    print(f"\n{color_text('📖 Оригинал:', Colors.BLUE)}")
    print(color_text(f"   {original}", Colors.CYAN))
    print(f"\n{color_text('✏️  Ваш текст:', Colors.BLUE)}")
    print(f"   {highlight_differences(original, user)}")
    print(f"\n{color_text('📌 Легенда:', Colors.YELLOW)} "
          f"{color_text('✓ правильно', Colors.GREEN)} | "
          f"{color_text('✗ ошибка', Colors.RED)}")

# ========== ЗАГРУЗКА ТЕКСТОВ ИЗ ФАЙЛА ==========
def load_texts():
    """Загружает тексты из файла texts.txt"""
    texts_file = Path("texts.txt")
    
    # Если файла нет — создаём с примерами
    if not texts_file.exists():
        print(color_text("\n⚠️ Файл texts.txt не найден! Создаю с примерами...", Colors.YELLOW))
        example_texts = [
            "Привет как дела",
            "Мама мыла раму",
            "Быстро печатать очень полезно для работы",
            "Клавиатура это инструмент программиста",
            "Сегодня отличная погода пойду гулять",
            "Python простой и мощный язык программирования"
        ]
        with open(texts_file, 'w', encoding='utf-8') as f:
            for text in example_texts:
                f.write(text + '\n')
        print(color_text("✅ Файл создан! Добавляй свои тексты в texts.txt", Colors.GREEN))
        time.sleep(2)
        return example_texts
    
    # Читаем тексты из файла
    texts = []
    with open(texts_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):  # # в начале — комментарий
                texts.append(line)
    
    if not texts:
        print(color_text("❌ Файл texts.txt пуст! Добавь хотя бы один текст.", Colors.RED))
        input("Нажми Enter для выхода...")
        sys.exit(1)
    
    return texts

def show_texts_menu(texts):
    """Показывает список доступных текстов"""
    print(f"\n{color_text('📚 Доступные тексты:', Colors.YELLOW + Colors.BOLD)}")
    for i, text in enumerate(texts, 1):
        preview = text[:50] + "..." if len(text) > 50 else text
        print(f"  {color_text(f'[{i}]', Colors.GREEN)} {preview}")
    print(f"  {color_text('[0]', Colors.BLUE)} Случайный текст")
    print(f"  {color_text('[q]', Colors.RED)} Выйти")

def main():
    clear_screen()
    print_fancy_header("ТРЕНАЖЁР СКОРОСТИ ПЕЧАТИ")
    
    # Загружаем тексты
    texts = load_texts()
    print(f"\n{color_text(f'✅ Загружено {len(texts)} текстов из файла texts.txt', Colors.GREEN)}")
    print(f"{color_text('💡 Чтобы добавить свой текст — открой texts.txt блокнотом и напиши новую строку', Colors.CYAN)}")
    
    input(f"\n{color_text('▶ Нажми Enter, чтобы начать...', Colors.CYAN)}")
    
    while True:
        clear_screen()
        show_texts_menu(texts)
        
        choice = input(f"\n{color_text('Выбери текст (номер или 0 для случайного): ', Colors.CYAN)}")
        
        if choice.lower() == 'q':
            clear_screen()
            print_fancy_header("СПАСИБО ЗА ТРЕНИРОВКУ!")
            print(f"\n{color_text('✨ Ты молодец! Продолжай практиковаться. ✨', Colors.GREEN + Colors.BOLD)}\n")
            sys.exit(0)
        
        try:
            idx = int(choice)
            if idx == 0:
                original_text = random.choice(texts)
            elif 1 <= idx <= len(texts):
                original_text = texts[idx - 1]
            else:
                print(color_text("❌ Неверный номер!", Colors.RED))
                time.sleep(1)
                continue
        except ValueError:
            print(color_text("❌ Введи число или q", Colors.RED))
            time.sleep(1)
            continue
        
        # Основной цикл тренировки с выбранным текстом
        while True:
            clear_screen()
            print_fancy_header("ПЕЧАТАЙ ТЕКСТ")
            print(f"\n{color_text('👉 Текст для печати:', Colors.YELLOW)}")
            print(color_text(f"\n   {original_text}\n", Colors.BOLD + Colors.CYAN))
            
            input(color_text('⏎ Готов? Нажми Enter и сразу начинай печатать!', Colors.GREEN))
            
            start_time = time.time()
            user_input = input(f"\n{color_text('✏️ Печатай сюда: ', Colors.BLUE)}")
            end_time = time.time()
            
            elapsed_seconds = end_time - start_time
            elapsed_minutes = elapsed_seconds / 60
            
            errors, error_percent, correct_words = calculate_errors(original_text, user_input)
            
            total_chars = len(original_text)
            speed_chars_per_min = int(total_chars / elapsed_minutes) if elapsed_minutes > 0 else 0
            total_words = len(original_text.split())
            
            clear_screen()
            print_fancy_header("РЕЗУЛЬТАТЫ ТРЕНИРОВКИ")
            print_colored_comparison(original_text, user_input)
            
            print(f"\n{color_text('═' * 60, Colors.CYAN)}")
            
            time_color = Colors.GREEN if elapsed_seconds < 30 else Colors.YELLOW if elapsed_seconds < 60 else Colors.RED
            print(f"{color_text('⏱️  Время:', Colors.BOLD)}          {color_text(f'{elapsed_seconds:.2f} секунд', time_color)}")
            
            speed_color = Colors.GREEN if speed_chars_per_min > 200 else Colors.YELLOW if speed_chars_per_min > 100 else Colors.RED
            print(f"{color_text('⚡ Скорость:', Colors.BOLD)}        {color_text(f'{speed_chars_per_min} знаков/мин', speed_color)}")
            
            words_color = Colors.GREEN if correct_words == total_words else Colors.YELLOW
            print(f"{color_text('✅ Правильных слов:', Colors.BOLD)}  {color_text(f'{correct_words} из {total_words}', words_color)}")
            
            errors_color = Colors.GREEN if errors == 0 else Colors.YELLOW if errors < 5 else Colors.RED
            print(f"{color_text('❌ Ошибок:', Colors.BOLD)}          {color_text(f'{errors} символов', errors_color)}")
            
            percent_color = Colors.GREEN if error_percent == 0 else Colors.YELLOW if error_percent < 10 else Colors.RED
            print(f"{color_text('📊 Процент ошибок:', Colors.BOLD)}   {color_text(f'{error_percent:.1f}%', percent_color)}")
            
            print(color_text("═" * 60, Colors.CYAN))
            
            print()
            if error_percent == 0:
                print(color_text("🎉 ИДЕАЛЬНО! Ошибок нет! Ты настоящий мастер печати! 🎉", Colors.GREEN + Colors.BOLD))
            elif error_percent < 10:
                print(color_text("👍 Отлично! Очень мало ошибок! Так держать!", Colors.GREEN))
            elif error_percent < 30:
                print(color_text("🙂 Хорошо, но можно точнее. Сосредоточься на точности.", Colors.YELLOW))
            else:
                print(color_text("😅 Многовато ошибок. Попробуй медленнее, но внимательнее.", Colors.RED))
            
            print(f"\n{color_text('Что дальше с этим текстом?', Colors.YELLOW)}")
            print(f"  {color_text('[Enter]', Colors.GREEN)} Ещё раз тот же текст")
            print(f"  {color_text('[n]', Colors.BLUE)} Выбрать другой текст")
            
            again = input(f"\n{color_text('Твой выбор: ', Colors.CYAN)}")
            if again.lower() == 'n':
                break
            # иначе повторяем тот же текст

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print(f"\n\n{color_text('👋 До встречи!', Colors.YELLOW)}\n")
        sys.exit(0)
