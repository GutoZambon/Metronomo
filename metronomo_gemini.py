import kivy
# kivy.require('2.0.0') # Descomente se precisar de uma versão específica

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout # Para posicionar o contador de ciclos
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, BooleanProperty, ListProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp # Para usar "density-independent pixels"

# Opcional: Definir um tamanho de janela para teste no Desktop
# Window.size = (400, 600)

class MetronomeLayout(BoxLayout):
    """
    Layout principal que contém a lógica e os widgets da interface.
    """
    # --- Propriedades Ligadas à Interface (.kv) ---
    total_cycles_input = StringProperty("4")  # Valor inicial como string para TextInput
    beats_per_cycle_input = StringProperty("4") # Valor inicial (2 ou 4)
    bpm_input = StringProperty("120")         # Valor inicial como string para TextInput

    # --- Propriedades de Estado Interno ---
    current_cycle = NumericProperty(0)
    current_beat = NumericProperty(0)
    total_cycles = NumericProperty(0)       # Valor numérico após iniciar
    beats_per_cycle = NumericProperty(0)    # Valor numérico após iniciar
    bpm = NumericProperty(0)                # Valor numérico após iniciar

    is_running = BooleanProperty(False)
    metronome_event = ObjectProperty(None, allownone=True) # Guarda o evento do Clock
    interval = NumericProperty(0.5)         # Intervalo em segundos (60 / BPM)

    # --- Propriedades Visuais ---
    beat_display_text = StringProperty("-")
    cycle_display_text = StringProperty("- / -")
    beat_area_color = ListProperty([0.8, 0.8, 0.8, 1]) # Cor de fundo inicial (RGBA)

    def start_stop(self):
        """Alterna entre iniciar e parar o metrônomo."""
        if self.is_running:
            self.stop_metronome()
        else:
            self.start_metronome()

    def validate_inputs(self):
        """Valida os inputs do usuário e atualiza as propriedades numéricas."""
        try:
            self.total_cycles = int(self.total_cycles_input)
            self.bpm = int(self.bpm_input)
            self.beats_per_cycle = int(self.beats_per_cycle_input) # Vem do Spinner

            if self.total_cycles <= 0:
                print("Erro: O número de ciclos deve ser positivo.")
                # Poderia mostrar um Popup de erro aqui
                return False
            if self.bpm <= 0:
                print("Erro: O BPM deve ser positivo.")
                return False
            if self.beats_per_cycle not in [2, 4]:
                 print("Erro: Número de tempos inválido (deve ser 2 ou 4).")
                 return False # Embora o Spinner limite, é bom validar

            return True
        except ValueError:
            print("Erro: Verifique se Ciclos e BPM são números inteiros válidos.")
            return False

    def start_metronome(self):
        """Inicia a contagem do metrônomo."""
        if not self.validate_inputs():
            return # Não inicia se a validação falhar

        print(f"Iniciando: {self.total_cycles} ciclos, {self.beats_per_cycle} tempos/ciclo, {self.bpm} BPM")

        self.interval = 60.0 / self.bpm
        self.current_cycle = 1
        self.current_beat = 0 # Começa em 0 para o primeiro update ir para 1
        self.is_running = True

        # Atualiza textos e estado dos botões/inputs
        self.ids.start_stop_button.text = "Parar"
        self.ids.cycles_input.disabled = True
        self.ids.beats_spinner.disabled = True
        self.ids.bpm_input.disabled = True

        # Agenda a função update_metronome para ser chamada repetidamente
        # Chama uma vez imediatamente para mostrar o primeiro tempo sem atraso
        self.update_metronome(0)
        # Agenda as próximas chamadas se houver mais de um tempo ou ciclo
        if self.total_cycles > 0 and (self.beats_per_cycle > 1 or self.total_cycles > 1):
             self.metronome_event = Clock.schedule_interval(self.update_metronome, self.interval)


    def stop_metronome(self):
        """Para a contagem do metrônomo."""
        print("Parando metrônomo.")
        if self.metronome_event:
            Clock.unschedule(self.metronome_event)
            self.metronome_event = None

        self.is_running = False
        self.current_cycle = 0
        self.current_beat = 0

        # Reseta textos e estado dos botões/inputs
        self.beat_display_text = "-"
        self.cycle_display_text = "- / -"
        self.beat_area_color = [0.8, 0.8, 0.8, 1] # Reseta cor de fundo
        self.ids.start_stop_button.text = "Iniciar"
        self.ids.cycles_input.disabled = False
        self.ids.beats_spinner.disabled = False
        self.ids.bpm_input.disabled = False

    def update_metronome(self, dt):
        """
        Chamado a cada batida (intervalo). Atualiza os contadores e a interface.
        dt: delta time desde a última chamada (não usado diretamente aqui).
        """
        if not self.is_running:
            # Segurança extra, caso seja chamado após parar
            self.stop_metronome()
            return

        # Avança a batida
        self.current_beat += 1

        # Verifica se o ciclo terminou
        if self.current_beat > self.beats_per_cycle:
            self.current_beat = 1 # Reinicia batida
            self.current_cycle += 1 # Avança ciclo

            # Verifica se todos os ciclos terminaram
            if self.current_cycle > self.total_cycles:
                self.stop_metronome()
                self.beat_display_text = "Fim" # Indica que terminou
                self.cycle_display_text = f"{self.total_cycles}/{self.total_cycles}"
                return # Sai da função

        # Atualiza a interface se ainda estiver rodando
        if self.is_running:
            self.beat_display_text = str(self.current_beat)
            self.cycle_display_text = f"{self.current_cycle}/{self.total_cycles}"

            # Muda a cor de fundo para feedback visual (exemplo simples)
            if self.current_beat == 1:
                # Cor diferente para a primeira batida do ciclo
                self.beat_area_color = [0.5, 0.8, 0.5, 1] # Verde claro
            else:
                 # Outra cor para as demais batidas
                self.beat_area_color = [0.6, 0.6, 0.9, 1] # Azul claro

class MetronomeApp(App):
    """Classe principal do aplicativo Kivy."""
    def build(self):
        # O Kivy automaticamente carrega o arquivo .kv com o mesmo nome
        # da classe App (sem o 'App'), em minúsculas: 'metronome.kv'
        return MetronomeLayout()

if __name__ == '__main__':
    MetronomeApp().run()