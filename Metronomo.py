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
from kivy.resources import resource_find

# Utilizando o SoundLoader do Kivy, que é multiplataforma.
# Isso simplifica o código, não precisando da verificação de sistema operacional.
from kivy.core.audio import SoundLoader

# Carregamos o som uma única vez para otimizar o desempenho.
sound_path = resource_find('bip.wav')
bip_sound = SoundLoader.load(sound_path) if sound_path else None

def emitir_bip():
    if bip_sound:
        bip_sound.play()
    else:
        print("Aviso: Arquivo 'bip.wav' não encontrado. Não será emitido som.")


class FullscreenDisplay(ModalView):
    remaining_time = NumericProperty(0)
    def __init__(self, tempo, ciclo, total_ciclos, cor, on_close=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.auto_dismiss = False
        layout = FloatLayout()
        box = BoxLayout()
        
        # Aumentamos a fonte para melhor visualização em tela cheia
        lbl = Label(text=str(tempo), font_size=150, color=(0, 0, 0, 1))
        lbl_ciclo = Label(text=f'Ciclo: {ciclo}/{total_ciclos}', size_hint=(None, None), size=(120, 40),
                          pos_hint={'center_x': 0.92, 'center_y': 0.95}, color=(0, 0, 0, 1), font_size=20)
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
        
        self.countdown_lbl = Label(text=f'{self.remaining_time:.2f}s', font_size=30,
                                   color=(0, 0, 0, 1), size_hint=(None, None),
                                   size=(100, 50), pos_hint={'center_x': 0.5, 'y': 0.05})
        layout.add_widget(self.countdown_lbl)
        
        self.add_widget(layout)
        # Agendamos a atualização do contador regressivo
        self.update_event = Clock.schedule_interval(self.update_countdown, 0.1)

    def close_modal(self, on_close):
        Clock.unschedule(self.update_event) # Para o contador ao fechar
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
        # Inputs para configuração
        self.ciclos = TextInput(text='10', hint_text='Quantidade de ciclos', input_filter='int', multiline=False)
        self.add_widget(Label(text='Ciclos:'))
        self.add_widget(self.ciclos)
        
        self.vezes_por_minuto = TextInput(text='80', hint_text='BPM (Batidas por Minuto)', input_filter='int', multiline=False)
        self.add_widget(Label(text='BPM (Batidas por Minuto):'))
        self.add_widget(self.vezes_por_minuto)
        
        # Dropdown para selecionar os tempos
        self.tempos_dropdown = DropDown()
        for t in ['2', '4', '8']:
            btn = Button(text=t, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: self.tempos_dropdown.select(btn.text))
            self.tempos_dropdown.add_widget(btn)
            
        self.tempos = Button(text='4') # Valor inicial
        self.tempos.bind(on_release=self.tempos_dropdown.open)
        self.tempos_dropdown.bind(on_select=lambda instance, x: setattr(self.tempos, 'text', x))
        self.add_widget(Label(text='Tempos por Ciclo:'))
        self.add_widget(self.tempos)

        # O CheckBox de respiro é mantido na interface, mas sua lógica será ignorada por enquanto
        respiro_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.respiro_checkbox = CheckBox(active=False)
        respiro_layout.add_widget(self.respiro_checkbox)
        respiro_layout.add_widget(Label(text='Respiro (Ignorado por enquanto)'))
        self.add_widget(respiro_layout)
        
        self.start_btn = Button(text='Iniciar', font_size=20, background_color=(0, 1, 0, 1))
        self.start_btn.bind(on_press=self.iniciar)
        self.add_widget(self.start_btn)
        
        self.tempo_atual = 0
        self.ciclo_atual = 0
        self.executando = False
        self.current_display = None
        
        # Dicionário de cores para cada tempo
        self.cores_tempos = {
            1: (57/255, 255/255, 20/255, 1),   # Verde Limão
            2: (255/255, 0/255, 255/255, 1),   # Magenta
            3: (0/255, 255/255, 255/255, 1),   # Ciano
            4: (255/255, 255/255, 0/255, 1),   # Amarelo
            5: (255/255, 117/255, 24/255, 1),  # Laranja
            6: (0/255, 98/255, 255/255, 1),    # Azul
            7: (125/255, 0/255, 255/255, 1),   # Roxo
            8: (255/255, 0/255, 0/255, 1)      # Vermelho
        }

    def iniciar(self, instance):
        # Validação de entradas
        try:
            self.total_ciclos = int(self.ciclos.text)
            self.total_tempos = int(self.tempos.text)
            self.vezes_por_minuto_val = int(self.vezes_por_minuto.text)
            if self.total_ciclos <= 0 or self.vezes_por_minuto_val <= 0:
                raise ValueError("Valores devem ser positivos.")
        except (ValueError, TypeError):
            self.popup('Erro', 'Preencha corretamente todos os campos com números positivos!')
            return
            
        # --- LÓGICA PRINCIPAL CORRIGIDA ---
        # O intervalo de cada batida é 60 segundos dividido pelo BPM.
        self.intervalo = 60.0 / self.vezes_por_minuto_val
        
        self.tempo_atual = 0 # Começará em 1 na primeira chamada
        self.ciclo_atual = 1
        self.executando = True
        
        # Desabilita o botão para evitar múltiplos cliques
        self.start_btn.disabled = True
        
        # Cancela qualquer agendamento anterior e inicia o novo ciclo
        Clock.unschedule(self.ciclo_visual)
        Clock.schedule_interval(self.ciclo_visual, self.intervalo)
        # Chama a primeira batida imediatamente
        self.ciclo_visual(0)

    def ciclo_visual(self, dt):
        if not self.executando:
            self.parar_execucao()
            return

        # Avança o tempo
        self.tempo_atual += 1

        # Verifica se o ciclo terminou
        if self.tempo_atual > self.total_tempos:
            self.ciclo_atual += 1
            self.tempo_atual = 1 # Reinicia o tempo para 1
            
            # Verifica se todos os ciclos foram concluídos
            if self.ciclo_atual > self.total_ciclos:
                self.parar_execucao()
                self.popup('Concluído', 'Ciclos finalizados!')
                return
        
        emitir_bip()
        self.update_display()
        
    def update_display(self):
        if self.current_display:
            self.current_display.dismiss()
        
        cor = self.cores_tempos.get(self.tempo_atual, (1, 1, 1, 1)) # Cor padrão branca
        
        self.current_display = FullscreenDisplay(
            tempo=self.tempo_atual,
            ciclo=self.ciclo_atual,
            total_ciclos=self.total_ciclos,
            cor=cor,
            on_close=self.parar_execucao
        )
        self.current_display.remaining_time = self.intervalo
        self.current_display.open()

    def parar_execucao(self, *args):
        self.executando = False
        Clock.unschedule(self.ciclo_visual)
        if self.current_display:
            self.current_display.dismiss()
            self.current_display = None
        self.start_btn.disabled = False # Reabilita o botão

    def popup(self, titulo, mensagem):
        popup = Popup(title=titulo, content=Label(text=mensagem), size_hint=(0.6, 0.4))
        popup.open()


class MetronomeApp(App):
    def build(self):
        return MetronomeScreen()

if __name__ == '__main__':
    MetronomeApp().run()