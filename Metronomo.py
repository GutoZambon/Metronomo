from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty
from plyer import audio
from kivy.resources import resource_find
import platform


if platform.system() == "Windows":
    from kivy.core.audio import SoundLoader
    def emitir_bip():
        path = resource_find('bip.wav')
        if path:
            sound = SoundLoader.load(path)
            if sound:
                sound.play()
else:
    from plyer import audio
    def emitir_bip():
        path = resource_find('bip.wav')
        if path:
            audio.play()

class FullscreenDisplay(ModalView):
    remaining_time = NumericProperty(0)
    def __init__(self, tempo, ciclo, total_ciclos, cor, respiro=False, on_close=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.auto_dismiss = False
        layout = FloatLayout()
        box = BoxLayout()
        lbl = Label(text='RESPIRE' if respiro else str(tempo), font_size=120, color=(0, 0, 0, 1))
        lbl_ciclo = Label(text=f'{ciclo}/{total_ciclos}', size_hint=(None, None), size=(80, 40),
                          pos_hint={'center_x': 0.95, 'center_y': 0.5}, color=(0, 0, 0, 1))
        close_btn = Button(text='X', size_hint=(None, None), size=(50, 50),
                           pos_hint={'right': 1, 'top': 1})
        close_btn.bind(on_press=lambda instance: self.close_modal(on_close))
        box.add_widget(lbl)
        with box.canvas.before:
            Color(*cor)
            self.rect = Rectangle(size=box.size, pos=box.pos)
        box.bind(pos=self.update_rect, size=self.update_rect)
        layout.add_widget(box)
        layout.add_widget(lbl_ciclo)
        layout.add_widget(close_btn)
        self.countdown_lbl = Label(text=f'{self.remaining_time:.1f}s', font_size=30,
                                   color=(0, 0, 0, 1), size_hint=(None, None),
                                   size=(100, 50), pos_hint={'center_x': 0.5, 'y': 0.05})
        layout.add_widget(self.countdown_lbl)
        self.add_widget(layout)
        Clock.schedule_interval(self.update_countdown, 0.1)
    def close_modal(self, on_close):
        self.dismiss()
        if on_close:
            on_close()
    def update_countdown(self, dt):
        self.remaining_time -= dt
        if self.remaining_time < 0:
            self.remaining_time = 0
        self.countdown_lbl.text = f'{self.remaining_time:.1f}s'
    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class MetronomeScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        self.ciclos = TextInput(text='10', hint_text='Quantidade de ciclos', input_filter='int', multiline=False)
        self.add_widget(self.ciclos)
        self.vezes_por_minuto = TextInput(text='13', hint_text='bpm', input_filter='int', multiline=False)
        self.add_widget(self.vezes_por_minuto)
        self.tempos_dropdown = DropDown()
        for t in ['2', '4', '8']:
            btn = Button(text=t, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.tempos_dropdown.select(btn.text))
            self.tempos_dropdown.add_widget(btn)
        self.tempos = Button(text='8')
        self.tempos.bind(on_release=self.tempos_dropdown.open)
        self.tempos_dropdown.bind(on_select=lambda instance, x: setattr(self.tempos, 'text', x))
        self.add_widget(self.tempos)
        respiro_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.respiro_checkbox = CheckBox(active=True)
        respiro_layout.add_widget(self.respiro_checkbox)
        respiro_layout.add_widget(Label(text='Respiro'))
        self.add_widget(respiro_layout)
        self.start_btn = Button(text='Iniciar')
        self.start_btn.bind(on_press=self.iniciar)
        self.add_widget(self.start_btn)
        self.tempo_atual = 0
        self.ciclo_atual = 0
        self.executando = False
        self.current_display = None
        self.cores_tempos = {
            1: (57/255, 255/255, 20/255, 1),
            2: (255/255, 0/255, 255/255, 1),
            3: (0/255, 255/255, 255/255, 1),
            4: (255/255, 255/255, 0/255, 1),
            5: (255/255, 117/255, 24/255, 1),
            6: (0/255, 98/255, 255/255, 1),
            7: (125/255, 0/255, 255/255, 1),
            8: (255/255, 0/255, 0/255, 1)
        }

    def iniciar(self, instance):
        try:
            self.total_ciclos = int(self.ciclos.text)
            self.total_tempos = int(self.tempos.text)
            self.vezes_por_minuto_val = int(self.vezes_por_minuto.text)
            if self.total_tempos not in [2, 4, 8]:
                raise ValueError
        except:
            self.popup('Erro', 'Preencha corretamente todos os campos!')
            return
        self.tempo_atual = 1
        self.ciclo_atual = 1
        self.intervalo = 60 / (self.vezes_por_minuto_val * self.total_tempos)
        self.executando = True
        Clock.unschedule(self.ciclo_visual)
        Clock.schedule_interval(self.ciclo_visual, self.intervalo)

    def ciclo_visual(self, dt):
        if not self.executando:
            Clock.unschedule(self.ciclo_visual)
            return
        if self.tempo_atual > self.total_tempos:
            if self.respiro_checkbox.active:
                self.update_display(respiro=True)
                Clock.unschedule(self.ciclo_visual)
                Clock.schedule_once(self.finalizar_respiro, self.intervalo)
                return
            else:
                self.proximo_ciclo()
        else:
            emitir_bip()
            self.update_display()
            self.tempo_atual += 1

    def finalizar_respiro(self, dt):
        self.proximo_ciclo()
        if self.executando:
            self.ciclo_visual(0)
            Clock.schedule_interval(self.ciclo_visual, self.intervalo)

    def proximo_ciclo(self):
        self.tempo_atual = 1
        if self.ciclo_atual >= self.total_ciclos:
            Clock.unschedule(self.ciclo_visual)
            self.executando = False
            if self.current_display:
                self.current_display.dismiss()
            self.popup('Concluído', 'Ciclos finalizados!')
        else:
            self.ciclo_atual += 1

    def update_display(self, respiro=False):
        if self.current_display:
            self.current_display.dismiss()
        cor = (1, 1, 1, 1) if respiro else self.cores_tempos.get(self.tempo_atual, (1, 1, 1, 1))
        self.current_display = FullscreenDisplay(
            tempo=self.tempo_atual,
            ciclo=self.ciclo_atual,
            total_ciclos=self.total_ciclos,
            cor=cor,
            respiro=respiro,
            on_close=self.parar_execucao
        )
        self.current_display.remaining_time = self.intervalo
        self.current_display.open()

    def parar_execucao(self):
        self.executando = False
        Clock.unschedule(self.ciclo_visual)

    def popup(self, titulo, mensagem):
        popup = Popup(title=titulo, content=Label(text=mensagem), size_hint=(0.6, 0.4))
        popup.open()

class MetronomeApp(App):
    def build(self):
        return MetronomeScreen()

if __name__ == '__main__':
    MetronomeApp().run()
