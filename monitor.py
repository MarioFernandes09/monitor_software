import psutil
import time
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

class MonitoramentoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitoramento de Software")
        self.root.state('zoomed')  # Maximiza a janela
        self.root.configure(bg="#f0f0f0")

        # Layout geral em duas colunas
        self.left_frame = tk.Frame(root, bg="#f0f0f0")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.right_frame = tk.Frame(root, bg="#f0f0f0", width=400)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # Título
        self.title_label = tk.Label(self.left_frame, text="Monitoramento de Software", font=("Arial", 16, "bold"), bg="#f0f0f0")
        self.title_label.pack(pady=10)

        # Frame de entrada
        self.input_frame = tk.Frame(self.left_frame, bg="#f0f0f0")
        self.input_frame.pack(pady=5)

        self.label_process = tk.Label(self.input_frame, text="Selecione o Processo:", font=("Arial", 12), bg="#f0f0f0")
        self.label_process.grid(row=0, column=0, padx=10, pady=5)

        processos = ["Visual Studio Code", "Google Chrome", "CPU", "Discord", "WhatsApp"]
        self.process_var = tk.StringVar()
        self.dropdown_process = ttk.Combobox(self.input_frame, textvariable=self.process_var, values=processos, font=("Arial", 12), width=25)
        self.dropdown_process.grid(row=0, column=1, padx=10, pady=5)
        self.dropdown_process.set("Selecione...")

        self.label_time = tk.Label(self.input_frame, text="Tempo (segundos):", font=("Arial", 12), bg="#f0f0f0")
        self.label_time.grid(row=1, column=0, padx=10, pady=5)
        self.entry_time = tk.Entry(self.input_frame, font=("Arial", 12))
        self.entry_time.grid(row=1, column=1, padx=10, pady=5)
        self.entry_time.insert(0, "30")

        # Botão iniciar
        self.button_start = tk.Button(self.left_frame, text="Iniciar Monitoramento", font=("Arial", 12), bg="#4CAF50", fg="white", command=self.iniciar_monitoramento)
        self.button_start.pack(pady=15)

        # Barra de progresso
        self.progress_bar = ttk.Progressbar(self.left_frame, length=400, mode="determinate")
        self.progress_bar.pack(pady=10)

        # Gráficos
        self.fig, self.ax = plt.subplots(2, 1, figsize=(6, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.left_frame)
        self.canvas.get_tk_widget().pack(pady=10, fill=tk.BOTH, expand=True)

        # Título Histórico
        self.history_label = tk.Label(self.right_frame, text="Histórico de Monitoramento", font=("Arial", 14, "bold"), bg="#f0f0f0")
        self.history_label.pack(pady=(10, 5))

        # Frame do histórico com listbox
        self.history_frame = tk.Frame(self.right_frame, bg="#f0f0f0")
        self.history_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.scrollbar = tk.Scrollbar(self.history_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_listbox = tk.Listbox(self.history_frame, font=("Arial", 11))
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.history_listbox.yview)

        # Botão limpar histórico
        self.button_clear = tk.Button(self.right_frame, text="Limpar Histórico", font=("Arial", 12), bg="#f44336", fg="white", command=self.limpar_historico)
        self.button_clear.pack(pady=10)

        # Variáveis
        self.cpu_data = []
        self.memory_data = []
        self.monitorando = False
        self.historico = []

    def iniciar_monitoramento(self):
        nome_processo = self.process_var.get()
        tempo = self.entry_time.get()

        if not nome_processo or nome_processo == "Selecione...":
            messagebox.showerror("Erro", "Selecione um processo para monitorar.")
            return

        if not tempo.isdigit():
            tempo = 30
        else:
            tempo = int(tempo)

        proc = self.encontrar_processo(nome_processo)
        if not proc:
            messagebox.showerror("Erro", f"Processo '{nome_processo}' não encontrado.")
            return

        self.monitorando = True
        self.cpu_data = []
        self.memory_data = []

        self.button_start.config(state=tk.DISABLED)
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = tempo

        threading.Thread(target=self.monitorar, args=(proc, tempo, nome_processo)).start()

    def monitorar(self, proc, duracao, nome_processo):
        for i in range(duracao):
            if not self.monitorando:
                break

            try:
                cpu = proc.cpu_percent(interval=1)
                memoria = proc.memory_info().rss / (1024 * 1024)
                self.cpu_data.append(cpu)
                self.memory_data.append(memoria)

                self.atualizar_grafico()
                self.progress_bar["value"] = i + 1

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                messagebox.showwarning("Aviso", "O processo foi finalizado ou está inacessível.")
                break

        self.finalizar_monitoramento(nome_processo, duracao)

    def finalizar_monitoramento(self, nome_processo, duracao):
        self.monitorando = False
        self.button_start.config(state=tk.NORMAL)

        cpu_medio = sum(self.cpu_data) / len(self.cpu_data) if self.cpu_data else 0
        mem_medio = sum(self.memory_data) / len(self.memory_data) if self.memory_data else 0
        resultado = f"CPU médio: {cpu_medio:.2f}%, Memória média: {mem_medio:.2f} MB"

        item = f"{nome_processo} - {duracao}s - {resultado}"
        self.historico.append(item)
        self.atualizar_historico()

        messagebox.showinfo("Monitoramento Finalizado", "O monitoramento foi concluído com sucesso!")

    def encontrar_processo(self, nome_processo):
        nomes_processos = {
            "Visual Studio Code": "Code.exe",
            "Google Chrome": "chrome.exe",
            "CPU": None,
            "Discord": "Discord.exe",
            "WhatsApp": "WhatsApp.exe",
        }

        alvo = nomes_processos.get(nome_processo)
        if nome_processo == "CPU":
            class CpuTotal:
                def cpu_percent(self, interval):
                    return psutil.cpu_percent(interval=interval)
                def memory_info(self):
                    mem = psutil.virtual_memory()
                    class MemInfo:
                        rss = mem.used
                    return MemInfo()
            return CpuTotal()

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and alvo and proc.info['name'].lower() == alvo.lower():
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def atualizar_grafico(self):
        self.ax[0].cla()
        self.ax[1].cla()

        self.ax[0].plot(self.cpu_data, label="Uso de CPU (%)")
        self.ax[0].set_title("Uso de CPU")
        self.ax[0].legend()

        self.ax[1].plot(self.memory_data, label="Uso de Memória (MB)", color="r")
        self.ax[1].set_title("Uso de Memória")
        self.ax[1].legend()

        self.canvas.draw()

    def atualizar_historico(self):
        self.history_listbox.delete(0, tk.END)
        for item in self.historico:
            self.history_listbox.insert(tk.END, item)

    def limpar_historico(self):
        self.historico.clear()
        self.history_listbox.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = MonitoramentoApp(root)
    root.mainloop()
