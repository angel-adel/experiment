import json
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle

# Цвета для кнопок
COLORS = {
    'white': (1, 1, 1, 1),
    'red': (1, 0.3, 0.3, 1),
    'green': (0.3, 0.8, 0.3, 1),
    'blue': (0.3, 0.5, 1, 1),
    'yellow': (1, 1, 0.3, 1),
    'orange': (1, 0.6, 0.2, 1),
    'purple': (0.7, 0.3, 1, 1),
    'black': (0.2, 0.2, 0.2, 1),
}

class FloatingButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "+"
        self.font_size = 40
        self.size_hint = (None, None)
        self.size = (70, 70)
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.9, 1)
        self.pos_hint = {'right': 1, 'bottom': 1}
        self.bind(pos=self.update_rounded_corners)
        
    def update_rounded_corners(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[35])

class ScriptButton(Button):
    def __init__(self, script, callback, **kwargs):
        super().__init__(**kwargs)
        self.script = script
        self.callback = callback
        self.text = script['name']
        self.size_hint_y = None
        self.height = 60
        self.background_normal = ''
        self.background_color = COLORS.get(script.get('color', 'white'), (1,1,1,1))
        
    def on_release(self):
        self.callback(self.script['text'])

class ScriptonizerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_file = "scripts_data.json"
        self.scripts = []
        self.load_scripts()
        
    def build(self):
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        
        # Основной слой с плавающей кнопкой
        main_layout = FloatLayout()
        
        # Контейнер для основного содержимого
        container = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(1, 1))
        
        # Верхняя панель с кнопками
        top_bar = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        btn_settings = Button(text='⚙️', size_hint_x=None, width=50)
        btn_settings.bind(on_release=self.show_about)
        top_bar.add_widget(btn_settings)
        
        btn_editor = Button(text='📝', size_hint_x=None, width=50)
        btn_editor.bind(on_release=self.open_editor)
        top_bar.add_widget(btn_editor)
        
        # Поле поиска
        self.search_input = TextInput(hint_text='🔍 Поиск...', multiline=False, size_hint_x=0.7)
        self.search_input.bind(text=self.filter_scripts)
        top_bar.add_widget(self.search_input)
        
        btn_add = Button(text='➕', size_hint_x=None, width=50, background_color=(0.3, 0.7, 0.3, 1))
        btn_add.bind(on_release=self.add_script)
        top_bar.add_widget(btn_add)
        
        container.add_widget(top_bar)
        
        # Область скриптов (прокручиваемая)
        self.scroll = ScrollView()
        self.scripts_grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.scripts_grid.bind(minimum_height=self.scripts_grid.setter('height'))
        self.scroll.add_widget(self.scripts_grid)
        container.add_widget(self.scroll)
        
        # Добавляем основной контейнер в FloatLayout
        main_layout.add_widget(container)
        
        # Плавающая кнопка
        self.fab = FloatingButton()
        self.fab.bind(on_release=self.add_script)
        main_layout.add_widget(self.fab)
        
        self.refresh_scripts()
        
        return main_layout
    
    def refresh_scripts(self):
        self.scripts_grid.clear_widgets()
        for script in self.scripts:
            btn = ScriptButton(script, self.copy_to_clipboard)
            self.scripts_grid.add_widget(btn)
    
    def filter_scripts(self, instance, value):
        self.scripts_grid.clear_widgets()
        search_text = value.lower()
        for script in self.scripts:
            if search_text in script['name'].lower() or search_text in script['text'].lower():
                btn = ScriptButton(script, self.copy_to_clipboard)
                self.scripts_grid.add_widget(btn)
    
    def copy_to_clipboard(self, text):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(text)
        self.show_popup("Готово!", "Текст скопирован в буфер обмена", 1)
    
    def show_popup(self, title, message, duration=2):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.3))
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), duration)
    
    def show_about(self, instance):
        self.show_popup("О программе", 
                       "Скриптонайзер\nВерсия 2.0 (Android)\n\n"
                       "• Хранение скриптов\n"
                       "• Копирование в буфер\n"
                       "• Поиск\n"
                       "• Плавающая кнопка", 3)
    
    def open_editor(self, instance):
        if not self.scripts:
            self.show_popup("Нет скриптов", "Сначала добавьте скрипты через +", 2)
            return
        
        # Создаем окно редактора
        editor_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Список скриптов
        scroll = ScrollView()
        list_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        list_layout.bind(minimum_height=list_layout.setter('height'))
        
        for i, script in enumerate(self.scripts):
            btn_frame = BoxLayout(size_hint_y=None, height=50, spacing=5)
            btn = Button(text=script['name'], background_color=COLORS.get(script.get('color', 'white'), (1,1,1,1)))
            btn.bind(on_release=lambda x, idx=i: self.edit_script(idx))
            btn_frame.add_widget(btn)
            
            del_btn = Button(text='🗑️', size_hint_x=None, width=50, background_color=(1, 0.3, 0.3, 1))
            del_btn.bind(on_release=lambda x, idx=i: self.delete_script(idx))
            btn_frame.add_widget(del_btn)
            
            list_layout.add_widget(btn_frame)
        
        scroll.add_widget(list_layout)
        editor_layout.add_widget(scroll)
        
        # Кнопки импорта/экспорта
        btn_bar = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_import = Button(text='📥 Импорт')
        btn_import.bind(on_release=self.import_scripts)
        btn_export = Button(text='📤 Экспорт')
        btn_export.bind(on_release=self.export_scripts)
        btn_bar.add_widget(btn_import)
        btn_bar.add_widget(btn_export)
        editor_layout.add_widget(btn_bar)
        
        popup = Popup(title='Редактор скриптов', content=editor_layout, size_hint=(0.9, 0.8))
        popup.open()
    
    def delete_script(self, index):
        self.scripts.pop(index)
        self.save_scripts()
        self.refresh_scripts()
        self.show_popup("Удалено", "Скрипт удален", 1)
    
    def edit_script(self, index):
        script = self.scripts[index]
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        layout.add_widget(Label(text='Имя скрипта:', size_hint_y=None, height=30))
        name_input = TextInput(text=script['name'], multiline=False)
        layout.add_widget(name_input)
        
        layout.add_widget(Label(text='Текст скрипта:', size_hint_y=None, height=30))
        text_input = TextInput(text=script['text'], multiline=True, size_hint_y=0.5)
        layout.add_widget(text_input)
        
        layout.add_widget(Label(text='Цвет:', size_hint_y=None, height=30))
        color_input = TextInput(text=script.get('color', 'white'), multiline=False, hint_text='white/red/green/blue/yellow/orange/purple/black')
        layout.add_widget(color_input)
        
        btn_save = Button(text='Сохранить', size_hint_y=None, height=50, background_color=(0.3, 0.7, 0.3, 1))
        
        popup = Popup(title=f'Редактировать: {script["name"]}', content=layout, size_hint=(0.9, 0.7))
        
        def save_and_close(instance):
            script['name'] = name_input.text
            script['text'] = text_input.text
            script['color'] = color_input.text if color_input.text in COLORS else 'white'
            self.save_scripts()
            self.refresh_scripts()
            popup.dismiss()
            self.show_popup("Сохранено", "Скрипт обновлен", 1)
        
        btn_save.bind(on_release=save_and_close)
        layout.add_widget(btn_save)
        popup.open()
    
    def add_script(self, instance):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        layout.add_widget(Label(text='Имя скрипта:', size_hint_y=None, height=30))
        name_input = TextInput(multiline=False)
        layout.add_widget(name_input)
        
        layout.add_widget(Label(text='Текст скрипта:', size_hint_y=None, height=30))
        text_input = TextInput(multiline=True, size_hint_y=0.5)
        layout.add_widget(text_input)
        
        layout.add_widget(Label(text='Цвет (white/red/green/blue/yellow/orange/purple/black):', size_hint_y=None, height=30))
        color_input = TextInput(text='white', multiline=False)
        layout.add_widget(color_input)
        
        btn_save = Button(text='Сохранить', size_hint_y=None, height=50, background_color=(0.3, 0.7, 0.3, 1))
        
        popup = Popup(title='Добавить скрипт', content=layout, size_hint=(0.9, 0.7))
        
        def save_and_close(instance):
            name = name_input.text
            text = text_input.text
            color = color_input.text if color_input.text in COLORS else 'white'
            if name and text:
                self.scripts.append({"name": name, "text": text, "color": color})
                self.save_scripts()
                self.refresh_scripts()
                popup.dismiss()
                self.show_popup("Успех", "Скрипт добавлен!", 1)
            else:
                self.show_popup("Ошибка", "Заполните имя и текст", 1)
        
        btn_save.bind(on_release=save_and_close)
        layout.add_widget(btn_save)
        popup.open()
    
    def import_scripts(self, instance):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        filechooser = FileChooserListView()
        layout.add_widget(filechooser)
        
        def load_selected(instance):
            if filechooser.selection:
                path = filechooser.selection[0]
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        imported = json.load(f)
                    self.scripts.extend(imported)
                    self.save_scripts()
                    self.refresh_scripts()
                    self.show_popup("Успех", f"Импортировано {len(imported)} скриптов", 2)
                    popup.dismiss()
                except Exception as e:
                    self.show_popup("Ошибка", f"Не удалось импортировать: {e}", 2)
        
        btn_load = Button(text='Загрузить', size_hint_y=None, height=50)
        btn_load.bind(on_release=load_selected)
        layout.add_widget(btn_load)
        
        popup = Popup(title='Выберите JSON файл', content=layout, size_hint=(0.9, 0.7))
        popup.open()
    
    def export_scripts(self, instance):
        from android.storage import primary_external_storage_path
        path = os.path.join(primary_external_storage_path(), 'Download', 'scripts_export.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.scripts, f, ensure_ascii=False, indent=2)
        self.show_popup("Экспорт", f"Сохранено в:\n{path}", 3)
    
    def save_scripts(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.scripts, f, ensure_ascii=False, indent=2)
    
    def load_scripts(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.scripts = json.load(f)
            except:
                self.scripts = []
        else:
            self.scripts = []

if __name__ == '__main__':
    ScriptonizerApp().run()
