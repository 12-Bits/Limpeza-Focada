import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
import os
import shutil
import subprocess
import sys
import urllib.parse
from datetime import datetime, timedelta
import Programa_Principal as principal
import LimpezaGeral as limpeza

BG_PADRAO ="#01303f"
BG_ATUAL = BG_PADRAO
FONT_PADRÃO= "#d4f0fc"
FONT_ATUAL = FONT_PADRÃO

class AvisoInicialScreen(tk.Toplevel):
    """Janela modal de aviso mostrada na primeira execução."""
    def __init__(self, master):
        super().__init__(master)
        self.configure(bg=BG_ATUAL)
        self.master = master
        self.title("Aviso Importante")

        # Centraliza a janela
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        pos_x = (largura_tela // 2) - (450 // 2)
        pos_y = (altura_tela // 2) - (250 // 2)
        self.geometry(f'600x350+{pos_x}+{pos_y}')
        self.resizable(False, False)

        # Variável para o Checkbox
        self.nao_mostrar_var = tk.BooleanVar()

        # --- Conteúdo ---
        main_frame = tk.Frame(self, padx=20, pady=20,bg=BG_ATUAL)
        main_frame.pack(fill='both', expand=True, )

        tk.Label(main_frame, text="⚠️ AVISO DE USO ⚠️", font=("TkDefaultFont", 20, "bold"), fg="#FF4500", bg=BG_ATUAL).pack(pady=5)

        texto_aviso = (

            "É extremamente recomendado escolher diretórios\n que não possuam programas portateis,\n"
            "ou especificar quais diretórios serão escaneados,\n"
            "já que arquivos deles podem ser excluidos acidentalmente."

        )
        tk.Label(main_frame, text=texto_aviso, bg=BG_ATUAL, font=("TkDefaultFont", 14, "bold"),fg=FONT_ATUAL, justify='center').pack(pady=10)

        tk.Checkbutton(
            main_frame,
            text="Não mostrar esta mensagem novamente",
            variable=self.nao_mostrar_var,

        ).pack(pady=10)

        tk.Button(main_frame, text="Entendi", command=self.fechar_e_salvar, bg="#c3f7c3").pack(pady=10, ipadx=10)

        # --- Configuração Modal ---
        # Impede interação com a janela principal
        self.grab_set()
        # Garante que fechar no "X" também chame a lógica de salvar
        self.protocol("WM_DELETE_WINDOW", self.fechar_e_salvar)

    def fechar_e_salvar(self):
        """
        Verifica o checkbox e salva a configuração se necessário,
        antes de fechar a janela de aviso.
        """
        print("Aviso fechando: liberando o controle...")
        if self.nao_mostrar_var.get():
            # Se o checkbox estiver marcado, atualiza o config
            try:
                config = principal.carregar_config()
                config["mostrar_aviso_inicial"] = False
                principal.salvar_config(config)
            except Exception as e:
                # Mesmo se falhar, o programa deve continuar
                print(f"Erro ao salvar config do aviso: {e}")
        try:
            self.master.grab_release()
        except:
            # Protege contra erros se o grab já foi liberado, mas é improvável
            pass
        # Libera a janela principal e destrói o aviso
        print("Aviso fechado, ConfigScreen deve continuar.")
        self.destroy()

class ConfigScreen(tk.Tk):
    """Tela inicial para coletar as pastas e a data limite."""
    def __init__(self):
        super().__init__()
        self.config(bg=BG_ATUAL)
        config = principal.carregar_config()

        # 1. Lógica do Aviso
        if config.get("mostrar_aviso_inicial", True):
            self.withdraw()
            aviso = AvisoInicialScreen(self)
            self.wait_window(aviso)

        # 2. Configurações da janela (fora do IF)
        self.title("Limpeza Focada")
        largura_janela = 400
        altura_janela = 600
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        pos_x = (largura_tela // 2) - (largura_janela // 2)
        pos_y = (altura_tela // 2) - (altura_janela // 2)
        self.geometry(f'{largura_janela}x{altura_janela}+{pos_x}+{pos_y}')
        self.minsize(300, 500)


        # ⭐️ 3. DEICONIFY PROTEGIDO (GARANTE VISIBILIDADE) ⭐️
        try:
            self.deiconify()
        except tk.TclError:
            pass
        self.periodos = {
            "6 Meses (Aproximado)": 180,
            "1 Ano (Aproximado)": 365,
            "2 Anos (Aproximado)": 730,
            "3 Anos (Aproximado)": 1095,
        }
        self.periodo_selecionado = tk.StringVar(self)
        self.periodo_selecionado.set("1 Ano (Aproximado)")

        # ------------------ FRAME PRINCIPAL SIMPLES ------------------
        self.frame_simples = tk.Frame(self, bg=BG_ATUAL)
        self.frame_simples.pack(pady=10, padx=10 )

        tk.Label(self.frame_simples, bg=BG_ATUAL, text="Limpeza Focada", font=("TkDefaultFont", 20, "bold"), fg=FONT_ATUAL).pack(pady=5)
        tk.Label(self.frame_simples, bg=BG_ATUAL, text="Início Rápido", font=("TkDefaultFont", 14, "bold"),fg=FONT_ATUAL).pack(pady=5)

        tk.Label(self.frame_simples, text="Pasta para Escaneamento Rápido:",  font=("TkDefaultFont", 12, "bold"), bg=BG_ATUAL, fg=FONT_ATUAL).pack(pady=10)

        pasta_rapida_atual = principal.carregar_config().get("pasta_padrao_rapido", "N/A")
        self.pasta_rapida_label = tk.Label(
            self.frame_simples,
            text=os.path.basename(pasta_rapida_atual),
            bg='lightyellow',
            anchor='center'
        )
        self.pasta_rapida_label.pack(pady=2)

        tk.Button(
            self.frame_simples,
            text="Alterar Pasta Padrão",
            command=self.alterar_pasta_rapida,
        ).pack(pady=5)

        # 1. Seleção de Data (Dropdown)
        tk.Label(self.frame_simples, text="Arquivos não modificados desde:",bg=BG_ATUAL, font=("TkDefaultFont", 12, "bold"), fg=FONT_ATUAL).pack(pady=5)
        opcoes = list(self.periodos.keys())
        tk.OptionMenu(self.frame_simples, self.periodo_selecionado, *opcoes).pack(pady=5)

        # 2. Botão para Opções Avançadas (Chama a Toplevel)
        tk.Button(self.frame_simples, text="Opções de Filtro Avançado",
                  command=self.abrir_tela_avancada).pack(pady=10)

        # 3. Botão para Limpeza Focada
        tk.Button(self.frame_simples, text="Limpeza Geral",
                  command=self.abrir_limpeza_focada).pack(pady=5)
        # 4. Botão principal de Escaneamento
        self.escaneamento_rapido_btn = tk.Button(
            self.frame_simples,
            text="Escanear e Gerenciar Agora",
            command=self.iniciar_escaneamento_rapido,
            bg="lightgreen", font=("TkDefaultFont", 10, "bold")
        )
        self.escaneamento_rapido_btn.pack(pady=10)

        # 5. Label de Carregamento (na raiz da janela, fora do frame)
        self.loading_label = tk.Label(self, bg=BG_ATUAL,text="", fg="blue")
        self.loading_label.pack()

        self.cancel_flag = threading.Event()

        self.cancel_btn = tk.Button(self.frame_simples, text="Parar Escaneamento", command=self.cancel_scan, state='disabled')
        self.cancel_btn.pack(pady=5,)
        self.scan_success = False

    def cancel_scan(self):
        self.cancel_flag.set()

    def _calcular_data_limite(self, periodo_texto):
        """
        Calcula a data limite no passado baseada no período selecionado (em dias).
        """
        # Usa o dicionário definido no __init__ para obter o número de dias
        dias = self.periodos.get(periodo_texto)

        if not dias:
            # Fallback
            dias = 30

        data_limite = datetime.now() - timedelta(days=dias)
        return data_limite.strftime("%Y-%m-%d")

    def abrir_limpeza_focada(self):
        """Esconde a janela principal e abre a Limpeza Focada."""
        self.scan_success = False
        self.withdraw()
        submenu = JunkCleanerScreen(self)
        self.wait_window(submenu)
        try:

            # Se o scan foi bem-sucedido, o flag estará True e não faremos nada.
            if not self.scan_success:
                self.deiconify() # Reaparece apenas se não foi destruída
        except tk.TclError:
            # Captura a exceção que ocorre quando a janela principal já foi destruída
            # e a ignora, permitindo que o programa continue o fechamento/transição.
            pass

    def alterar_pasta_rapida(self):
        """Permite ao usuário selecionar e salvar uma nova pasta padrão para o modo rápido."""

        # Pega a pasta atual para definir o diretório inicial
        config = principal.carregar_config()
        caminho_inicial = config["pasta_padrao_rapido"] if os.path.isdir(config["pasta_padrao_rapido"]) else os.path.expanduser("~")

        # Abre o diálogo de seleção de pasta
        nova_pasta = filedialog.askdirectory(
            title="Selecione a nova Pasta Padrão para Escaneamento Rápido",
            initialdir=caminho_inicial
        )

        if nova_pasta:
            # 1. Atualiza a configuração e salva
            config["pasta_padrao_rapido"] = nova_pasta
            principal.salvar_config(config)

            # 2. Atualiza o Label na GUI
            self.pasta_rapida_label.config(text=os.path.basename(nova_pasta))
            messagebox.showinfo("Configuração Salva", f"Nova pasta padrão definida para: {os.path.basename(nova_pasta)}")

    def selecionar_pasta(self):
        """Abre o diálogo para selecionar uma ou mais pastas."""

        # Obtém o caminho da pasta atual para sugerir no pop-up
        caminho_inicial = self.pastas_selecionadas_str.get()
        if caminho_inicial == "Nenhuma pasta selecionada.":
            # Se for a primeira vez, sugere o Desktop do usuário
            caminho_inicial = os.path.expanduser("~")

        # Usa filedialog.askdirectory() para selecionar PASTA
        pasta_selecionada = filedialog.askdirectory(
            title="Selecione a Pasta para Escanear",
            initialdir=caminho_inicial
        )

        if pasta_selecionada:
            self.pastas_selecionadas_str.set(pasta_selecionada)

    def iniciar_escaneamento_rapido(self):
        """Executa o escaneamento com pastas e data padrão (sem a tela de filtro)."""
        # 1. Obtenha pastas e data padrão que você quer usar
        pasta_rapida = principal.carregar_config()["pasta_padrao_rapido"]
        pastas_padrao_list = [pasta_rapida]
        pastas_padrao_str = ",".join(pastas_padrao_list)
        periodo_texto = self.periodo_selecionado.get()
        data_padrao_str = self._calcular_data_limite(periodo_texto)

        self.cancel_flag.clear()
        self.cancel_btn.config(state='normal')

        # 2. Inicia o escaneamento na thread, como você faz no iniciar_escaneamento
        self.escaneamento_rapido_btn.config(state='disabled', text="Escaneando...")
        self.loading_label.config(text="Aguarde: Escaneando arquivos grandes com filtro padrão...",bg=BG_ATUAL)

        threading.Thread(target=self.processar_escaneamento,
                         args=(pastas_padrao_str, data_padrao_str, self, self.cancel_flag, None),
                         daemon=True).start()

    def processar_escaneamento(self, pastas_str, data_str, parent_window=None, cancel_flag=None, pastas_ignorar=None):
        if parent_window is None:
            parent_window = self

        if pastas_ignorar is None:
            pastas_ignorar = []

        pastas = [p.strip() for p in pastas_str.split(",")]

        try:
                data_limite = datetime.strptime(data_str, "%Y-%m-%d")
        except ValueError:
                self.after(0, lambda: messagebox.showerror("Erro", "Formato de data inválido. Use AAAA-MM-DD."))

                if parent_window == self:
                     self.after(0, self.reabilitar_gui)
                else:
                     # Chama a nova função de reabilitar da janela avançada
                     self.after(0, parent_window.reabilitar_gui_avancado)
                return

        if cancel_flag and cancel_flag.is_set():
            if parent_window == self:
                self.after(0, self.reabilitar_gui)
            else:
                self.after(0, parent_window.reabilitar_gui_avancado)

            self.after(0, lambda: self.cancel_btn.config(state='disabled')) # Desabilita o da tela principal
            return

        # Chamada da função pesada
        arquivos = principal.listar_arquivos(
                pastas,
                data_limite,
                cancel_flag=cancel_flag,
                pastas_ignorar=pastas_ignorar
        )

        if cancel_flag and cancel_flag.is_set():
            if parent_window == self:
                self.after(0, self.reabilitar_gui)
            else:
                self.after(0, parent_window.reabilitar_gui_avancado)

            self.after(0, lambda: self.cancel_btn.config(state='disabled'))
            return

        self.after(0, lambda: self.abrir_gerenciador(arquivos, parent_window))

    def reabilitar_gui(self):
        """Função auxiliar para reabilitar a GUI em caso de erro no modo RÁPIDO."""
        self.escaneamento_rapido_btn.config(state='normal', text="Escanear e Gerenciar Agora")
        self.loading_label.config(text="", bg=BG_ATUAL) # Limpa o rótulo de carregamento

    def abrir_gerenciador(self, arquivos, parent_window):
        """Função que abre a próxima tela, chamada após a Thread terminar."""

        # --- 1. LIDAR COM CASO SEM ARQUIVOS ---
        if not arquivos:
            messagebox.showinfo(
                "Info",
                "Nenhum arquivo encontrado que se encaixe no filtro ou nenhuma pasta válida fornecida."
            )
            if parent_window == self:
                self.reabilitar_gui() # Reabilita a ConfigScreen (Modo Simples)
            else:
                parent_window.destroy() # Fecha o submenu (Modo Avançado/Limpeza Focada)
            return

        # --- 2. DESABILITAR UI E PREPARAR TRANSIÇÃO ---

        # Se o botão de cancelar da ConfigScreen existir, desabilite-o.
        if self.cancel_btn.winfo_exists():
            self.cancel_btn.config(state='disabled')

        # --- 3. EXECUTAR TRANSIÇÃO (DESTRUIÇÃO + CRIAÇÃO) ---

        # Se o escaneamento veio do MODO SIMPLES (ConfigScreen é a parent)
        if parent_window == self:
            self.scan_success = True  # Sinaliza destruição intencional
            self.destroy()            # Destrói o tk.Tk principal (ConfigScreen)

            # Inicia o FileManagerApp como a nova janela principal
            app = FileManagerApp(arquivos)
            app.mainloop()

        # Se o escaneamento veio de um SUBMENU (Avançado ou Limpeza Focada)
        else:
            # A transição é sempre para a FileManagerApp como nova principal.

            # 3a. Destrói o Submenu Toplevel
            parent_window.destroy()

            # 3b. Destrói a ConfigScreen (que estava escondida ou esperando no wait_window)
            self.scan_success = True
            self.destroy()

            # 3c. Inicia o FileManagerApp como a nova janela principal
            app = FileManagerApp(arquivos)
            app.mainloop()

    def abrir_tela_avancada(self):
        """Abre a janela de configuração avançada (Toplevel)."""
        self.scan_success = False
        self.withdraw() # 1. Esconde
        submenu = AdvancedFilterScreen(self)
        self.wait_window(submenu) # 2. PAUSA aqui até o submenu fechar

        try:
            # Se o scan foi bem-sucedido, o flag estará True e não faremos nada.
            if not self.scan_success:
                self.deiconify() # Reaparece apenas se não foi destruída
        except tk.TclError:
            # Captura a exceção que ocorre quando a janela principal já foi destruída
            # e a ignora, permitindo que o programa continue o fechamento/transição.
            pass

class FileManagerApp(tk.Tk):
    def __init__(self, arquivos):
        super().__init__()
        self.config(bg=BG_ATUAL)
        self.title("Gerenciador de Arquivos")
        largura_janela = 1050
        altura_janela = 500

        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        self.minsize(700, 300)
        pos_x = (largura_tela // 2) - (largura_janela // 2)
        pos_y = (altura_tela // 2) - (altura_janela // 2)
        self.geometry(f'{largura_janela}x{altura_janela}+{pos_x}+{pos_y}')

        self.arquivos = arquivos
        self.acoes = {arq: ("Manter", None) for arq in arquivos}
        self.config = principal.carregar_config()

        self.pasta_destino_padrao = tk.StringVar(self)
        self.pasta_destino_padrao.set(self.config.get("pasta_destino_padrao", os.path.expanduser("~")))

        # ======== Layout base (grid) ========
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # -------------------- FRAME PRINCIPAL DE DADOS (Treeview) --------------------
        self.frame_lista_container = tk.Frame(self, bg=BG_ATUAL)
        self.frame_lista_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Definindo as colunas
        colunas = ("Acao", "NomeArquivo", "Tamanho", "DataModificacao", "Destino")
        self.tree = ttk.Treeview(self.frame_lista_container, columns=colunas, show='headings')

        # Configuração das colunas
        self.tree.heading("Acao", text="Ação")
        self.tree.heading("NomeArquivo", text="Nome do Arquivo")
        self.tree.heading("Tamanho", text="Tamanho")
        self.tree.heading("DataModificacao", text="Última Modificação")
        self.tree.heading("Destino", text="Destino (Mover)")

        # Configuração das larguras
        self.tree.column("Acao", width=80, anchor='center')
        self.tree.column("NomeArquivo", width=300, anchor='w')
        self.tree.column("Tamanho", width=100, anchor='e')
        self.tree.column("DataModificacao", width=120, anchor='center')
        self.tree.column("Destino", width=200, anchor='w')

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(self.frame_lista_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Posicionamento
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        for col_id in colunas:
            # O Treeview passa o column ID e o evento. Usaremos apenas o ID.
            self.tree.heading(col_id, command=lambda c=col_id: self.ordenar_coluna(c))

        # Variável para controlar a direção da ordenação
        self.ordenacao_reversa = False

        # ⭐️ Evento de clique: Chama o menu de contexto ou a ação ⭐️
        self.tree.bind('<Button-1>', self.abrir_menu_contexto)

        # -------------------- FRAME INFERIOR (resumo + botão fixo) --------------------
        self.frame_inferior = tk.Frame(self, bg=BG_PADRAO)
        self.frame_inferior.grid(row=1, column=0, sticky="ew", pady=8)

        # Label do resumo
        self.resumo_label = tk.Label(
            self.frame_inferior,
            text="Resumo: todos os arquivos marcados como Manter",
            bg="white",
            font=("TkDefaultFont", 10, "italic"),
        )
        self.resumo_label.pack(pady=3)

        # Botão de executar
        tk.Button(
            self.frame_inferior,
            text="Executar Ações",
            command=self.executar_acoes,
            bg="lightblue",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(pady=5)

        # Cria lista de arquivos
        self.gerar_lista()

        # Garante que o resumo é preenchido e atualizado
        self.atualizar_resumo()

    def gerar_lista(self):
        """Preenche o Treeview com os dados dos arquivos."""
        for arquivo in self.arquivos:
            try:
                # 1. Obtém dados
                tamanho = os.path.getsize(arquivo)
                tamanho_str = self.formatar_tamanho(tamanho)
                data_mod = os.path.getmtime(arquivo)
                data_str = datetime.fromtimestamp(data_mod).strftime("%d/%m/%Y %H:%M")

                # 2. Insere a linha no Treeview
                # A última coluna 'AcoesBotoes' terá apenas um placeholder para o menu.
                item_id = self.tree.insert("", tk.END, text=arquivo, values=(
                    "Manter",
                    os.path.basename(arquivo),
                    tamanho_str,
                    data_str,
                    ""
                ))

                # 3. Armazena o ID do item para mapear de volta ao arquivo.
                # O text do item já é o caminho completo (arquivo)

                # Define a tag de cor inicial (verde para Manter)
                self.tree.tag_configure('Manter', background='#c3f7c3')
                self.tree.item(item_id, tags=('Manter',))

            except Exception as e:
                # Trata erros (como arquivo deletado enquanto o programa estava aberto)
                print(f"Erro ao obter dados para {arquivo}: {e}")

    def ordenar_coluna(self, col_id):
        """Reordena os itens no Treeview baseado na coluna clicada."""

        # 1. Inverte a direção da ordenação para a próxima vez
        self.ordenacao_reversa = not self.ordenacao_reversa

        # 2. Obtém todos os itens e ARMAZENA SEUS DADOS COMPLETOS
        data = []
        col_index = self.tree["columns"].index(col_id)

        for item_id in self.tree.get_children(''):

            # Obtém todos os dados do item ANTES de deletar
            item_info = self.tree.item(item_id)
            values = item_info['values']

            # Armazena o valor de ordenação, o ID e os dados completos
            data.append({
                'sort_value': values[col_index],
                'id': item_id,
                'text': item_info['text'],
                'values': values,
                'tags': item_info['tags']
            })

        # 3. Define a função de conversão/tipo de dado
        def obter_valor_ordenavel(item):
            # item['sort_value'] é o valor que está na coluna de ordenação
            valor_str = item['sort_value']

            if col_id == "Tamanho":
                return self._converter_tamanho_para_ordenacao(valor_str)

            elif col_id == "DataModificacao":
                try:
                    return datetime.strptime(valor_str, "%d/%m/%Y %H:%M")
                except:
                    return datetime.min

            elif col_id in ["Acao", "NomeArquivo", "Destino"]:
                return valor_str.lower()

            return valor_str

        # 4. Ordena os dados (usando a nova lista de dicionários)
        data.sort(key=obter_valor_ordenavel, reverse=self.ordenacao_reversa)

        # 5. Redesenha a lista no Treeview

        # Deleta todos os itens existentes da TELA
        self.tree.delete(*self.tree.get_children(''))

        # Insere os itens na ordem correta, usando os dados armazenados
        for item in data:
            # Reinsere a linha. O iid é importante para manter o item_id original.
            self.tree.insert('', tk.END,
                             iid=item['id'],
                             text=item['text'],
                             values=item['values'],
                             tags=item['tags'])

        # 6. Atualiza o cabeçalho
        direcao = '↑' if not self.ordenacao_reversa else '↓'
        for col in self.tree["columns"]:
            texto_atual = self.tree.heading(col, 'text')
            texto_limpo = texto_atual.replace('↑', '').replace('↓', '')

            self.tree.heading(col, text=texto_limpo)
        texto_coluna_clicada = self.tree.heading(col_id, 'text')
        self.tree.heading(col_id, text=texto_coluna_clicada + " " + direcao)

    def _converter_tamanho_para_ordenacao(self, tamanho_str):
        """Converte tamanho formatado (ex: '16.00 MB') para bytes para ordenação numérica."""
        if not tamanho_str or tamanho_str == '-':
            return 0

        try:
            partes = tamanho_str.split()
            valor = float(partes[0].replace(',', '.'))
            unidade = partes[1].upper()

            if unidade == 'B':
                return valor
            elif unidade == 'KB':
                return valor * 1024
            elif unidade == 'MB':
                return valor * (1024 ** 2)
            # Adicione mais unidades se necessário (GB, TB)

        except:
            return 0 # Retorna zero se a conversão falhar

        return 0

    def abrir_menu_contexto(self, event):
        """Mostra o menu de contexto ao clicar na linha do Treeview."""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        self.tree.selection_remove(self.tree.selection())
        self.tree.selection_set(item_id)

        #Força a atualização da GUI para desenhar o realce azul imediatamente
        self.update_idletasks()
        # Obtém o caminho completo do arquivo (armazenado no 'text' do item)
        arquivo = self.tree.item(item_id, 'text')

        # Cria e exibe o menu
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Manter", command=lambda a=arquivo, i=item_id: self.definir_acao_tree(a, i, "Manter", None))
        menu.add_command(label="Eliminar", command=lambda a=arquivo, i=item_id: self.definir_acao_tree(a, i, "Eliminar", None))
        menu.add_command(label="Mover...", command=lambda a=arquivo, i=item_id: self.definir_acao_mover_avancado_tree(a, i))
        menu.add_separator()
        menu.add_command(label="Ver na Pasta", command=lambda a=arquivo: self.abrir_pasta(a))

        # Exibe o menu na posição do clique
        try:
            menu.tk.call("tk_popup", menu, event.x_root, event.y_root)
        finally:
            self.tree.selection_remove(item_id)
            menu.grab_release()

    def definir_acao_tree(self, arquivo, item_id, acao, destino=None):
        """Define a ação e atualiza o Treeview."""
        self.acoes[arquivo] = (acao, destino)

        # 1. Atualiza os valores na linha do Treeview
        valores_atuais = list(self.tree.item(item_id, 'values'))
        valores_atuais[0] = acao # Coluna 'Acao'
        valores_atuais[4] = destino if destino else "" # Coluna 'Destino'
        self.tree.item(item_id, values=valores_atuais)

        # 2. Define a tag de cor
        tag = acao
        cores = {
            "Manter": "#c3f7c3",
            "Eliminar": "#f5b2b2",
            "Mover": "#b2d7f5",
        }
        self.tree.tag_configure(tag, background=cores.get(tag, 'white'))
        self.tree.item(item_id, tags=(tag,))

        self.atualizar_resumo()

    def definir_acao_mover_avancado_tree(self, arquivo, item_id):
        """Abre o diálogo para selecionar a pasta de destino antes de registrar a ação no Treeview."""

        # Usa o último caminho conhecido como inicial
        pasta_padrao = self.pasta_destino_padrao.get()

        destino = filedialog.askdirectory(
            title=f"Selecione a Pasta de Destino para: {os.path.basename(arquivo)}",
            initialdir=pasta_padrao if os.path.isdir(pasta_padrao) else None
        )

        if destino:
            # Salva o novo destino padrão (para usar na próxima vez)
            self.pasta_destino_padrao.set(destino)
            self.config["pasta_destino_padrao"] = destino
            principal.salvar_config(self.config) # Salva no arquivo de config

            # Chama a função para registrar e atualizar o Treeview
            self.definir_acao_tree(arquivo, item_id, "Mover", destino)
        else:
            # Se cancelar, mantém a ação atual
            pass # O menu não registra nada se for cancelado.


    def executar_acoes(self):
        """Executa todas as ações escolhidas pelo usuário de uma vez."""
        contagem = {"Manter": 0, "Eliminar": 0, "Mover": 0}
        arquivos_para_deletar = []
        arquivos_para_mover_com_destino = []

        # 1. Classificação das Ações
        for arquivo, (acao, destino) in self.acoes.items():
            contagem[acao] += 1
            if acao == "Eliminar":
                arquivos_para_deletar.append(arquivo)
            elif acao == "Mover":
                if destino:
                    arquivos_para_mover_com_destino.append((arquivo, destino))
                else:
                    contagem["Manter"] += 1
                    contagem["Mover"] -= 1

        # 2. Confirmação
        confirmar = messagebox.askyesno(
            "Confirmar execução",
            f"Tem certeza que deseja executar as ações?\n\n"
            f"- {contagem['Eliminar']} arquivos serão eliminados\n"
            f"- {contagem['Mover']} arquivos serão movidos\n"
            f"- {contagem['Manter']} arquivos serão mantidos\n\n"
            f"Essa ação não poderá ser desfeita.",
        )
        if not confirmar:
            return

        # 3. EXECUÇÃO DE MOVIMENTOS
        for arquivo, destino in arquivos_para_mover_com_destino:
            try:
                arquivo_normalizado = os.path.normpath(arquivo)
                destino_normalizado = os.path.normpath(destino)
                os.makedirs(destino_normalizado, exist_ok=True)
                shutil.move(arquivo_normalizado, destino_normalizado)
                print(f"Movido: {arquivo_normalizado}")
            except Exception as e:
                print(f"Erro ao mover: {e}")

        # 4. EXECUÇÃO DE EXCLUSÕES (COM CÁLCULO DE ESPAÇO) ⭐️
        total_bytes_liberados = 0  # Variável acumuladora

        if arquivos_para_deletar:
            for arquivo in arquivos_para_deletar:
                try:
                    arquivo_normalizado = os.path.normpath(arquivo)

                    # ⭐️ 1. Pega o tamanho ANTES de deletar
                    if os.path.exists(arquivo_normalizado):
                        tamanho = os.path.getsize(arquivo_normalizado)
                        total_bytes_liberados += tamanho

                    # 2. Deleta o arquivo
                    os.remove(arquivo_normalizado)
                    print(f"Deletado: {arquivo_normalizado}")

                except Exception as e:
                    print(f"Erro ao deletar {arquivo_normalizado}: {e}")

        # 5. Formatar o Texto de Espaço Liberado ⭐️
        texto_espaco = ""
        if total_bytes_liberados > 0:
            # Reutiliza sua função formatar_tamanho existente na classe
            tamanho_formatado = self.formatar_tamanho(total_bytes_liberados)
            texto_espaco = f"\n\nEspaço liberado em disco: {tamanho_formatado}"

        messagebox.showinfo(
            "Concluído",
            f"Todas as ações foram executadas.{texto_espaco}"
        )
        self.destroy()

    def formatar_tamanho(self, bytes_):
        """Converte tamanho em string legível."""
        if bytes_ < 1024:
            return f"{bytes_} B"
        elif bytes_ < 1024**2:
            return f"{bytes_//1024} KB"
        else:
            return f"{bytes_/(1024**2):.2f} MB"

    def abrir_pasta(self, arquivo):
        """
        Abre o explorador de arquivos e tenta selecionar o arquivo.
        """
        caminho_absoluto = os.path.abspath(arquivo)
        caminho_normalizado = os.path.normpath(caminho_absoluto)

        if not os.path.exists(caminho_absoluto):
            messagebox.showerror(
                "Erro de Caminho",
                f"O arquivo não foi encontrado no local esperado:\n{caminho_absoluto}"
            )
            return

        # --- Lógica Específica da Plataforma ---

        if sys.platform == "win32":

            # 1. Escapa o caminho inteiro com aspas duplas, crucial para nomes complexos
            caminho_escapado = f'"{caminho_normalizado}"'

            # 2. Constrói o comando COMPLETO como uma única string para o shell
            comando_completo = f'explorer /select,{caminho_escapado}'

            try:
                # shell=True resolve problemas de parsing de aspas e espaços.
                subprocess.run(comando_completo, shell=True)
            except Exception as e:
                messagebox.showerror("Erro de Comando", f"Falha ao executar o explorer: {e}")

        elif sys.platform == "darwin":
            # Comando para abrir a pasta no macOS
            pasta = os.path.dirname(caminho_absoluto)
            subprocess.run(["open", pasta])

        else:
            # Comando padrão para Linux
            pasta = os.path.dirname(caminho_absoluto)
            subprocess.run(["xdg-open", pasta])

    def atualizar_resumo(self):
        """Atualiza o texto acima do botão com um resumo das escolhas."""
        total = len(self.acoes)
        manter = sum(1 for acao, destino in self.acoes.values() if acao == "Manter")
        eliminar = sum(1 for acao, destino in self.acoes.values() if acao == "Eliminar")
        mover = sum(1 for acao, destino in self.acoes.values() if acao == "Mover")

        texto = (
            f"Resumo: {total} arquivos - "
            f"{manter} manter, {eliminar} eliminar, {mover} mover"
        )
        self.resumo_label.config(text=texto)

class AdvancedFilterScreen(tk.Toplevel):
    """Nova janela para exibir as opções de filtro avançado (pastas e data)."""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Filtros Avançados")
        self.config = principal.carregar_config()
        self.configure(bg=BG_ATUAL)

        self.pastas_bloqueadas = []
        self.extensoes_ignoradas = []

        # Define um tamanho padrão, mas a barra de rolagem lidará com o conteúdo
        largura, altura = 450, 600
        self.centralizar(largura, altura)
        self.minsize(450, 400)

        self.protocol("WM_DELETE_WINDOW", self.on_fechar_limpo)

        # --- ESTRUTURA DA BARRA DE ROLAGEM ---

        # 1. Frame principal que segura o canvas e a scrollbar
        main_frame = tk.Frame(self, bg=BG_ATUAL)
        main_frame.pack(fill='both', expand=True)

        # 2. Canvas
        self.canvas = tk.Canvas(main_frame, bg=BG_ATUAL)
        self.canvas.pack(side='left', fill='both', expand=True)

        self.canvas.bind("<Configure>", self.on_canvas_resize)

         # 3. Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.canvas.yview)
        scrollbar.pack(side='right', fill='y')

        # Configura o canvas para usar a scrollbar
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # 4. Frame Interno (onde TODO o conteúdo vai)
        #O parent de todos os widgets agora é self.scrollable_frame
        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_ATUAL)

        # Armazene o ID da janela criada ⭐️
        self.scrollable_window_id = self.canvas.create_window(
        (0, 0),
        window=self.scrollable_frame,
        anchor='nw',
        width=0)

        # Binds para a rolagem funcionar
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        # --- FIM DA ESTRUTURA DE ROLAGEM ---

        # Variável para armazenar o caminho da(s) pasta(s)
        self.pastas_selecionadas_str = tk.StringVar(self, value="Selecione a(s) pasta(s)")

        # ------------------ CONTEÚDO AVANÇADO (Parent = self.scrollable_frame) ------------------
        tk.Label(self.scrollable_frame, text="Filtros Avançados",bg=BG_ATUAL,fg=FONT_ATUAL, font=("TkDefaultFont", 14, "bold")).pack(pady=10)

        # INÍCIO DA NOVA SEÇÃO DE MÚLTIPLAS PASTAS
        tk.Label(self.scrollable_frame, font=("TkDefaultFont", 12, "bold"), text="Pastas para Escanear:", bg=BG_ATUAL,fg=FONT_ATUAL).pack(pady=5)

        # Frame para a Listbox e Scrollbar (caso os caminhos sejam longos)
        frame_pastas_scan = tk.Frame(self.scrollable_frame)
        frame_pastas_scan.pack(pady=5, padx=10, fill='x', expand=True)

        scan_scrollbar = tk.Scrollbar(frame_pastas_scan, orient='vertical')
        self.pastas_scan_listbox = tk.Listbox(frame_pastas_scan, height=5, yscrollcommand=scan_scrollbar.set)
        scan_scrollbar.config(command=self.pastas_scan_listbox.yview)

        scan_scrollbar.pack(side='right', fill='y')
        self.pastas_scan_listbox.pack(side='left', fill='x', expand=True)

        # Frame para os botões de Adicionar/Remover
        frame_botoes_scan = tk.Frame(self.scrollable_frame, bg=BG_ATUAL)
        frame_botoes_scan.pack()

        tk.Button(frame_botoes_scan, text="Adicionar Pasta...",   command=self.adicionar_pasta_scan).pack(side='left', padx=5, pady=5)
        tk.Button(frame_botoes_scan, text="Remover Selecionada", command=self.remover_pasta_scan).pack(side='left', padx=5, pady=5)

        # Entrada de Data Limite
        tk.Label(self.scrollable_frame, font=("TkDefaultFont", 12, "bold"), text="Data Limite (AAAA-MM-DD):",  fg=FONT_ATUAL, bg=BG_ATUAL).pack(pady=5)
        self.data_entry = tk.Entry(self.scrollable_frame)
        self.data_entry.pack(pady=5, padx=10, fill='x',expand=True)
        self.data_entry.insert(0, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))

        # --- Bloco de Pastas (Parent = self.scrollable_frame) ---
        pasta_frame = tk.Frame(self.scrollable_frame, bg=BG_ATUAL)
        pasta_frame.pack(pady=10, padx=10, fill='x')
        tk.Label(pasta_frame, font=("TkDefaultFont", 12, "bold"), text="Pastas a Ignorar (Blacklist)", fg=FONT_ATUAL, bg=BG_ATUAL).pack()

        add_pasta_frame = tk.Frame(pasta_frame)
        add_pasta_frame.pack(pady=5)
        self.pasta_entry = tk.Entry(add_pasta_frame, width=30)
        self.pasta_entry.pack(side='left', padx=5)
        tk.Button(add_pasta_frame, text="Selecionar Pasta", command=self.selecionar_pasta_bloqueada).pack(side='left')

        self.pasta_listbox = tk.Listbox(pasta_frame, height=5)
        self.pasta_listbox.pack(pady=5, fill='x', expand=True)
        self._carregar_pastas_bloqueadas()
        tk.Button(pasta_frame, text="Remover Selecionada", command=self.remover_pasta_bloqueada).pack()

        # --- Bloco de Extensões (Parent = self.scrollable_frame) ---
        ext_frame = tk.Frame(self.scrollable_frame,bg=BG_ATUAL)
        ext_frame.pack(pady=10, padx=10, fill='x')
        tk.Label(ext_frame,font=("TkDefaultFont", 12, "bold"), text="Ignorar Extensões (ex: .log, .tmp)",fg=FONT_ATUAL, bg=BG_ATUAL).pack()

        add_ext_frame = tk.Frame(ext_frame)
        add_ext_frame.pack (pady=5)
        self.ext_entry = tk.Entry(add_ext_frame, width=20)
        self.ext_entry.pack(side='left', padx=5)
        tk.Button(add_ext_frame, text="Adicionar Extensão", command=self.adicionar_extensao).pack(side='left')

        self.ext_listbox = tk.Listbox(ext_frame, height=4)
        self.ext_listbox.pack(pady=5, fill='x', expand=True)
        self._carregar_extensoes_ignoradas()
        tk.Button(ext_frame, text="Remover Selecionada", command=self.remover_extensao_selecionada).pack()

        # Botão Escanear
        self.escaneamento_btn = tk.Button(
            self.scrollable_frame,
            text="Escanear com Filtro",
            command=self.iniciar_escaneamento_avancado,
            bg='lightgreen',
            font=("TkDefaultFont", 10, "bold")
        )
        self.escaneamento_btn.pack(pady=10)

        self.cancel_btn_avancado = tk.Button(
            self.scrollable_frame,
            text="❌ Parar Escaneamento",
            command=self.cancelar_escaneamento,
            state='disabled' # Começa desabilitado
        )
        self.cancel_btn_avancado.pack(pady=5)

        self.loading_label = tk.Label(self.scrollable_frame, bg=BG_ATUAL, text="", fg="blue")
        self.loading_label.pack(pady=5)

    # --- FUNÇÕES DA BARRA DE ROLAGEM ---
    def on_frame_configure(self, event):
        """Atualiza a região de rolagem do canvas."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mouse_wheel(self, event):
        """Permite rolar com o scroll do mouse."""
        # 'event.delta' é 120 para scroll para cima, -120 para baixo no Windows
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def on_fechar_limpo(self):
        """Apenas limpa o bind do mouse e destrói a janela."""
        self.canvas.unbind_all("<MouseWheel>") # Impede que o bind continue
        self.destroy() # Fechar a janela fará o 'wait_window' continuar

    # --- FIM DAS FUNÇÕES DA BARRA DE ROLAGEM ---

    def on_canvas_resize(self, event):
        """Ajusta a largura do frame interno para que ele preencha a largura do canvas."""
        # Usa o ID da janela que armazenamos para forçar a largura
        self.canvas.itemconfigure(self.scrollable_window_id, width=event.width)

        # Chamamos o on_frame_configure logo em seguida para garantir que o scrollregion seja recalculado.
        self.on_frame_configure(event)

    def centralizar(self, largura, altura):
        """Função para centralizar a janela Toplevel."""
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        pos_x = (largura_tela // 2) - (largura // 2)
        pos_y = (altura_tela // 2) - (altura // 2)
        self.geometry(f'{largura}x{altura}+{pos_x}+{pos_y}')

    def _carregar_extensoes_ignoradas(self):
        """Carrega a lista de extensões do config e preenche o Listbox."""
        config = principal.carregar_config()
        self.extensoes_ignoradas = config.get("extensoes_ignoradas", [])
        self.ext_listbox.delete(0, tk.END) # Limpa a lista antes de preencher
        for ext in self.extensoes_ignoradas:
            self.ext_listbox.insert(tk.END, ext)

    def adicionar_extensao(self):
        """Adiciona uma extensão à blacklist."""
        ext = self.ext_entry.get().strip().lower()
        if not ext:
            return

        # Garante que a extensão comece com um ponto
        if not ext.startswith('.'):
            ext = '.' + ext

        if ext in self.extensoes_ignoradas:
            messagebox.showwarning("Duplicado", f"A extensão '{ext}' já está na lista.")
            return

        # Adiciona à lista da sessão e ao Listbox
        self.extensoes_ignoradas.append(ext)
        self.ext_listbox.insert(tk.END, ext)
        self.ext_entry.delete(0, tk.END)

        # Salva a lista atualizada no config.json
        config = principal.carregar_config()
        config["extensoes_ignoradas"] = self.extensoes_ignoradas
        principal.salvar_config(config)
        messagebox.showinfo("Sucesso", f"Extensão '{ext}' adicionada à blacklist.")

    def remover_extensao_selecionada(self):
        """Remove a extensão selecionada da blacklist."""
        selecionado_indices = self.ext_listbox.curselection()
        if not selecionado_indices:
            messagebox.showerror("Erro", "Nenhuma extensão selecionada para remover.")
            return

        indice = selecionado_indices[0]
        ext = self.ext_listbox.get(indice)

        # Remove da lista da sessão e do Listbox
        self.extensoes_ignoradas.remove(ext)
        self.ext_listbox.delete(indice)

        # Salva a lista atualizada no config.json
        config = principal.carregar_config()
        config["extensoes_ignoradas"] = self.extensoes_ignoradas
        principal.salvar_config(config)
        messagebox.showinfo("Sucesso", f"Extensão '{ext}' removida da blacklist.")

    def adicionar_pasta_scan(self):
        """Abre o diálogo para selecionar uma pasta e ADICIONA na lista."""
        pasta_selecionada = filedialog.askdirectory(
            title="Selecione a Pasta para Escanear"
        )

        if not pasta_selecionada:
            return  # Usuário cancelou

        # Verifica se a pasta está na blacklist ou em pastas fixas bloqueadas
        if principal.pasta_bloqueada(pasta_selecionada):
            messagebox.showerror(
                "Pasta bloqueada",
                f"A pasta selecionada não pode ser analisada:\n\n{pasta_selecionada}"
            )
            return  # Não deixa prosseguir

        # Verifica se já está na lista
        pastas_atuais = self.pastas_scan_listbox.get(0, tk.END)
        if pasta_selecionada in pastas_atuais:
            messagebox.showwarning("Duplicado", "Essa pasta já está na lista.")
            return

        # Caso contrário, aceita a pasta e adiciona na Listbox
        self.pastas_scan_listbox.insert(tk.END, pasta_selecionada)

    def remover_pasta_scan(self):
        """Remove a pasta selecionada da LISTA DE ESCANEAMENTO."""
        selecionado_indices = self.pastas_scan_listbox.curselection()
        if not selecionado_indices:
            messagebox.showerror("Erro", "Nenhuma pasta selecionada para remover.")
            return

        # Remove o item selecionado (índice 0, pois geralmente é seleção única)
        self.pastas_scan_listbox.delete(selecionado_indices[0])

    def iniciar_escaneamento_avancado(self):
        """Inicia o escaneamento a partir desta janela."""
        pastas_list = self.pastas_scan_listbox.get(0, tk.END)
        data_str = self.data_entry.get().strip()

        if not pastas_list or not data_str:
            messagebox.showerror("Erro", "Adicione pelo menos uma pasta e preencha a data.")
            return

        pastas_str = ",".join(pastas_list)

        self.escaneamento_btn.config(state='disabled')
        self.cancel_btn_avancado.config(state='normal') # Habilita o "Parar"
        self.master.cancel_flag.clear() # Limpa a flag
        self.loading_label.config(text="Escaneando... Por favor, aguarde.")

        # Passa 'self' como parent_window (AdvancedFilterScreen)
        threading.Thread(target=self.master.processar_escaneamento,
                                 args=(pastas_str, data_str, self, self.master.cancel_flag, self.pastas_bloqueadas), # Passa pastas_bloqueadas
                                 daemon=True).start()

    def _carregar_pastas_bloqueadas(self):
        """Carrega a lista de pastas bloqueadas do config e preenche o Listbox."""
        config = principal.carregar_config()
        # Assumindo que a chave 'pastas_bloqueadas' já está em Programa_Principal.py
        self.pastas_bloqueadas = config.get("pastas_bloqueadas", [])
        self.pasta_listbox.delete(0, tk.END) # Limpa a lista antes de preencher
        for pasta in self.pastas_bloqueadas:
            self.pasta_listbox.insert(tk.END, pasta)

    def selecionar_pasta_bloqueada(self):
        """Abre o diálogo para selecionar uma pasta para adicionar à blacklist."""
        pasta = filedialog.askdirectory(title="Selecione a Pasta para Ignorar")

        if not pasta:
            return

        # Normaliza o caminho para garantir consistência (ex: sem barra no final)
        pasta_normalizada = os.path.normpath(pasta)

        if pasta_normalizada in self.pastas_bloqueadas:
            messagebox.showwarning("Duplicado", f"A pasta '{pasta_normalizada}' já está na lista.")
            return

        # Adiciona à lista da sessão e ao Listbox
        self.pastas_bloqueadas.append(pasta_normalizada)
        self.pasta_listbox.insert(tk.END, pasta_normalizada)

        # Salva a lista atualizada no config.json
        config = principal.carregar_config()
        config["pastas_bloqueadas"] = self.pastas_bloqueadas
        principal.salvar_config(config)
        messagebox.showinfo("Sucesso", f"Pasta '{pasta_normalizada}' adicionada à blacklist.")

    def remover_pasta_bloqueada(self):
        """Remove a pasta selecionada da blacklist."""
        selecionado_indices = self.pasta_listbox.curselection()
        if not selecionado_indices:
            messagebox.showerror("Erro", "Nenhuma pasta selecionada para remover.")
            return

        indice = selecionado_indices[0]
        pasta = self.pasta_listbox.get(indice)

        # Remove da lista da sessão e do Listbox
        self.pastas_bloqueadas.remove(pasta)
        self.pasta_listbox.delete(indice)

        # Salva a lista atualizada no config.json
        config = principal.carregar_config()
        config["pastas_bloqueadas"] = self.pastas_bloqueadas
        principal.salvar_config(config)
        messagebox.showinfo("Sucesso", f"Pasta '{pasta}' removida da blacklist.")

        # Método para reabilitar esta GUI
    def reabilitar_gui_avancado(self):
        self.escaneamento_btn.config(state='normal')
        self.cancel_btn_avancado.config(state='disabled')
        self.loading_label.config(text="Escaneamento cancelado.")

        # Método para o botão parar
    def cancelar_escaneamento(self):
        self.loading_label.config(text="Cancelando...")
        self.master.cancel_flag.set() # Define a flag principal

class EmptyFoldersViewer(tk.Toplevel):
    """Janela para listar e confirmar a exclusão de pastas vazias."""
    def __init__(self, master, lista_pastas, callback_excluir):
        super().__init__(master)
        self.master = master
        self.callback_excluir = callback_excluir # Função para chamar se o usuário confirmar
        self.lista_pastas = lista_pastas

        self.title("Pastas Vazias Encontradas")
        self.geometry("800x500") # Aumentei o tamanho para melhor visualização
        self.configure(bg=BG_ATUAL)
        self.centralizar(800, 500) # Assumindo que você tem o método centralizar

        # Cabeçalho
        tk.Label(self, text=f"Foram encontradas {len(lista_pastas)} pastas vazias. Selecione as que deseja excluir:",
                 bg=BG_ATUAL, fg=FONT_ATUAL, font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        # Frame da Lista
        frame_lista = tk.Frame(self, bg=BG_ATUAL)
        frame_lista.pack(fill="both", expand=True, padx=10)

        # Scrollbar e Listbox
        scrollbar = tk.Scrollbar(frame_lista, orient="vertical")

        # ⭐️ MUDANÇA: 'selectmode=multiple' permite selecionar vários itens
        self.listbox = tk.Listbox(frame_lista, yscrollcommand=scrollbar.set, selectmode="multiple",
                                  height=20, bg=BG_ATUAL, fg=FONT_ATUAL)
        scrollbar.config(command=self.listbox.yview)

        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        # ⭐️ NOVO: Adiciona o Menu de Contexto (clique com o botão direito) ⭐️
        self.menu_contexto = tk.Menu(self.listbox, tearoff=0)
        self.menu_contexto.add_command(label="Abrir Localização da Pasta", command=self.abrir_pasta_selecionada)
        self.listbox.bind("<Button-3>", self.mostrar_menu_contexto) # Liga o clique direito

        # Preencher a lista e selecionar todos por padrão
        for pasta in lista_pastas:
            self.listbox.insert(tk.END, pasta)
            self.listbox.selection_set(tk.END) # Seleciona todos os itens ao carregar

        # Botões de Ação
        frame_botoes = tk.Frame(self, bg=BG_ATUAL)
        frame_botoes.pack(pady=10)

        tk.Button(frame_botoes, text="Cancelar", command=self.destroy, width=15).pack(side="left", padx=10)

        # ⭐️ MUDANÇA: O botão agora chama 'remover_selecionadas'
        tk.Button(frame_botoes, text="Excluir Selecionadas",
                  command=self.remover_selecionadas,
                  bg="#ffcccc", fg="red", width=20).pack(side="left", padx=10)

        # Botões de Seleção (Opcional, mas útil)
        tk.Button(frame_botoes, text="Selecionar Todas", command=self.selecionar_todas, width=15).pack(side="left", padx=10)
        tk.Button(frame_botoes, text="Limpar Seleção",
          command=lambda: self.listbox.selection_clear(0, tk.END), # Adiciona os argumentos 0 e tk.END
          width=15).pack(side="left", padx=10)

    # ----------------------------------------------------
    # ⭐️ FUNÇÕES NOVAS PARA ABRIR E SELECIONAR ⭐️
    # ----------------------------------------------------

    def centralizar(self, largura, altura):
                """Função para centralizar a janela Toplevel."""
                largura_tela = self.winfo_screenwidth()
                altura_tela = self.winfo_screenheight()
                pos_x = (largura_tela // 2) - (largura // 2)
                pos_y = (altura_tela // 2) - (altura // 2)
                self.geometry(f'{largura}x{altura}+{pos_x}+{pos_y}')

    def mostrar_menu_contexto(self, event):
        """Exibe o menu de contexto na posição do clique direito."""
        # Seleciona o item clicado para que a função de abrir saiba qual é
        try:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.listbox.nearest(event.y))
            self.menu_contexto.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_contexto.grab_release()

    def abrir_pasta_selecionada(self):
        """Abre a pasta selecionada no explorador de arquivos do sistema."""
        indices = self.listbox.curselection()
        if indices:
            pasta = self.listbox.get(indices[0]) # Pega apenas o primeiro item selecionado

            # Usa o módulo os.startfile (Windows) ou subprocess.run (outros sistemas)
            if sys.platform == "win32":
                os.startfile(pasta)
            else: # Linux, macOS
                try:
                    subprocess.run(["xdg-open", pasta], check=True) # Linux
                except FileNotFoundError:
                    subprocess.run(["open", pasta], check=True) # macOS

            # Limpa a seleção após a ação (opcional)
            self.listbox.selection_clear(0, tk.END)

    def selecionar_todas(self):
        """Seleciona todos os itens da lista."""
        self.listbox.selection_set(0, tk.END)

    def remover_selecionadas(self):
        """Obtém os itens selecionados e chama o callback de exclusão."""

        # Obtém os índices dos itens selecionados
        indices_selecionados = self.listbox.curselection()

        if not indices_selecionados:
            messagebox.showwarning("Aviso", "Nenhuma pasta foi selecionada para exclusão.")
            return

        # Constrói a lista de caminhos selecionados
        pastas_para_deletar = [self.listbox.get(i) for i in indices_selecionados]

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir as {len(pastas_para_deletar)} pastas selecionadas?\nEssa ação não pode ser desfeita."):
            self.destroy() # Fecha a lista
            # Chama a função principal de deletar, passando SOMENTE as pastas selecionadas
            self.callback_excluir(pastas_para_deletar)



class JunkCleanerScreen(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.configure(bg=BG_ATUAL)

        self.title("Limpeza Geral")
        largura, altura = 300, 650
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        pos_x = (largura_tela // 2) - (largura // 2)
        pos_y = (altura_tela // 2) - (altura // 2)
        self.geometry(f'{largura}x{altura}+{pos_x}+{pos_y}')
        self.minsize(450, 600)

        self.arquivos_lixo = []

        tk.Label(self, text="Opções de Limpeza Geral:", bg=BG_ATUAL,  fg=FONT_ATUAL, font=("TkDefaultFont", 14, "bold")).pack(pady=10)

        tk.Label(self, text="Arquivos Temporarios:", bg=BG_ATUAL,  fg=FONT_ATUAL, font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        self.scan_btn = tk.Button(self, text="Escanear Lixo", command=self.iniciar_escaneamento_lixo)
        self.scan_btn.pack(pady=5)

        self.loading_label = tk.Label(self, text="",bg=BG_ATUAL)
        self.loading_label.pack(pady=5)

        tk.Label(self, text="Remover Pastas Vazias:", bg=BG_ATUAL, fg=FONT_ATUAL, font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        # Variável para guardar a pasta selecionada
        self.pasta_vazias_alvo = tk.StringVar(self, value="Selecione uma pasta...")

        frame_vazias = tk.Frame(self, bg=BG_ATUAL)
        frame_vazias.pack(pady=5)

        tk.Button(frame_vazias, text="Selecionar Pasta", command=self.selecionar_pasta_para_vazias).pack(side='left', padx=5)
        self.lbl_pasta_vazias = tk.Label(frame_vazias, textvariable=self.pasta_vazias_alvo, bg="white", width=25, anchor='w')
        self.lbl_pasta_vazias.pack(side='left')

        self.btn_scan_vazias = tk.Button(self, text="Buscar Pastas Vazias", command=self.iniciar_escaneamento_vazias, bg="lightyellow")
        self.btn_scan_vazias.pack(pady=5)

        tk.Label(self, text="Escaneamento de Programas:", bg=BG_ATUAL,  fg=FONT_ATUAL, font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        # Frame de Seleção de Programa
        frame_programas = tk.Frame(self)
        frame_programas.pack(pady=10, padx=10, fill="both", expand=True)

        tk.Label(frame_programas, text="Programas Instalados Detectados:").pack()

        # Scrollbar e Listbox
        scrollbar = tk.Scrollbar(frame_programas, orient="vertical")
        self.programas_listbox = tk.Listbox(frame_programas, yscrollcommand=scrollbar.set, height=8)
        scrollbar.config(command=self.programas_listbox.yview)

        scrollbar.pack(side="right", fill="y")
        self.programas_listbox.pack(side="left", fill="both", expand=True)

        # Dicionário para mapear nome da lista para caminho
        self.mapa_programas = {}

        # Frame de Opções
        frame_opcoes = tk.Frame(self)
        frame_opcoes.pack(pady=10, padx=10)

        tk.Label(frame_opcoes, text="Arquivos não acessados há (meses):").pack(side="left", padx=5)
        self.meses_entry = tk.Entry(frame_opcoes, width=5)
        self.meses_entry.insert(0, "6") # Padrão de 6 meses
        self.meses_entry.pack(side="left")

        self.scan_btn = tk.Button(self, text="Escanear Programa Selecionado",
                                  command=self.iniciar_escaneamento_programa,
                                  font=("TkDefaultFont", 10, "bold"), bg="lightblue")
        self.scan_btn.pack(pady=10)

        self.loading_label = tk.Label(self,bg=BG_ATUAL, text="", fg="blue")
        self.loading_label.pack()

        # Preenche a lista
        self.preencher_lista_programas()

    def iniciar_escaneamento_lixo(self):
        # Desabilita o botão e mostra status
        self.scan_btn.config(state='disabled', text="Escaneando...")
        self.loading_label.config(text="Procurando arquivos temporários...")

        # Executa o escaneamento na thread para não travar a GUI
        threading.Thread(target=self.processar_escaneamento_lixo, daemon=True).start()

    def processar_escaneamento_lixo(self):
        # Chama a função pesada do novo módulo
        self.arquivos_lixo = limpeza.escanear_arquivos_temporarios()

        # Retorna para a thread principal (GUI)
        self.after(0, self.mostrar_resultados_lixo)

    def mostrar_resultados_lixo(self):
        if not self.winfo_exists():
            return

        self.scan_btn.config(state='normal', text="Escanear Lixo")

        total_lixo = len(self.arquivos_lixo)

        if total_lixo == 0:
            self.loading_label.config(text="✅ Nenhum lixo encontrado.")
            return

        confirmar = messagebox.askyesno(
            "Limpeza Encontrada",
            f"Encontrados {total_lixo} itens de lixo digital. Deseja deletar todos agora?",
            icon='warning'
        )

        if confirmar:
            # Chama a execução na thread novamente, se a exclusão for demorada
            self.loading_label.config(text="Deletando...")
            threading.Thread(target=self.executar_limpeza_lixo, daemon=True).start()
        else:
            self.loading_label.config(text="Limpeza cancelada.")

    def executar_limpeza_lixo(self):
        bytes_liberados, removidos = limpeza.executar_limpeza(self.arquivos_lixo)

        # Retorna para a thread principal (GUI)
        self.after(0, lambda: self.limpeza_concluida(bytes_liberados, removidos))

    def limpeza_concluida(self, bytes_liberados, removidos):
        if not self.winfo_exists():
            return

        # Usando um valor simples em MB para o exemplo:
        mb_liberados = bytes_liberados / (1024 * 1024)

        messagebox.showinfo(
            "Concluído",
            f"Limpeza concluída! \n{removidos} arquivos removidos.\nEspaço liberado: {mb_liberados:.2f} MB"
        )
        self.destroy()
    def preencher_lista_programas(self):
        """Busca os programas (pode demorar um pouco) e preenche a lista."""
        self.loading_label.config(text="Buscando programas no registro... Aguarde.")

        # Usamos o 'after' para dar tempo da GUI atualizar antes da busca
        self.after(100, self.buscar_e_preencher)

    def buscar_e_preencher(self):
        self.mapa_programas = limpeza.obter_pastas_programas_instalados()

        # Ordena por nome do programa
        nomes_ordenados = sorted(self.mapa_programas.keys(), key=str.lower)

        for nome in nomes_ordenados:
            caminho = self.mapa_programas[nome]
            # Mostra "Nome (Caminho)"
            self.programas_listbox.insert(tk.END, f"{nome}  ({caminho})")

        self.loading_label.config(text=f"Encontrados {len(nomes_ordenados)} programas.")

    def iniciar_escaneamento_programa(self):
        selecionado_indices = self.programas_listbox.curselection()
        if not selecionado_indices:
            messagebox.showerror("Erro", "Nenhum programa selecionado para escanear.")
            return

        try:
            meses = int(self.meses_entry.get())
            if meses <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Número de meses inválido.")
            return

        # Pega o texto completo do item selecionado
        texto_item = self.programas_listbox.get(selecionado_indices[0])

        # Extrai o nome do programa (o que vem antes do " (C:\...")
        nome_programa = texto_item.split("  (")[0]

        # Pega o caminho do nosso mapa
        pasta_para_escanear = self.mapa_programas.get(nome_programa)

        if not pasta_para_escanear or not os.path.isdir(pasta_para_escanear):
             messagebox.showerror("Erro", f"Caminho não encontrado para: {nome_programa}")
             return

        # Calcula a data limite
        data_limite = datetime.now() - timedelta(days=meses * 30.44) # Aproximação

        self.scan_btn.config(state="disabled", text="Escaneando...")
        self.loading_label.config(text=f"Escaneando {pasta_para_escanear}...")

        # Pega a flag de cancelamento da janela principal
        cancel_flag = self.master.cancel_flag
        cancel_flag.clear()
        self.master.cancel_btn.config(state='normal') # Habilita o botão "Parar" na janela principal

        # Inicia o escaneamento na thread
        threading.Thread(target=self.processar_escaneamento_programa,
                         args=(nome_programa, pasta_para_escanear, data_limite, cancel_flag),
                         daemon=True).start()

    def processar_escaneamento_programa(self, nome_programa, pasta, data_limite, cancel_flag):
        """Função que roda na thread."""

        arquivos, total_files = limpeza.encontrar_arquivos_nao_acessados(
            pasta,
            data_limite,
            cancel_flag
        )

        if cancel_flag.is_set():
            self.after(0, self.reabilitar_gui)
            return

        proporcao_nao_usada = 0
        if total_files > 0:
            proporcao_nao_usada = len(arquivos) / total_files

        if proporcao_nao_usada > 0.5 and total_files > 0:
            # Chama a função de sugestão na thread principal (GUI)
            self.after(0, lambda: self.sugerir_desinstalacao(nome_programa, arquivos))

        # Caso contrário, mostra o gerenciador de arquivos
        else:

            self.master.after(0, lambda: self.master.abrir_gerenciador(arquivos, self))

    def reabilitar_gui(self):
        self.scan_btn.config(state="normal", text="Escanear Programa Selecionado")
        self.loading_label.config(text="Escaneamento cancelado.")
        self.master.cancel_btn.config(state='disabled') # Desabilita o "Parar" da principal

    def sugerir_desinstalacao(self, nome_programa, arquivos_para_gerenciador):
        """
        Pergunta ao usuário se deseja desinstalar o app, pois a maioria dos
        arquivos parece não ser usada.
        """
        # Reabilita a GUI principal (botão Parar)
        self.reabilitar_gui()

        resposta = messagebox.askyesno(
            "Programa Pouco Utilizado?",
            f"A análise sugere que a maioria dos arquivos de '{nome_programa}' não é acessada há muito tempo (desde o período configurado).\n\n"
            "Deseja abrir 'Aplicativos e Recursos' para desinstalá-lo?\n\n",
            parent=self # Garante que a messagebox fique sobre esta janela
        )

        if resposta:
            # Usuário quer desinstalar
            self.abrir_app_features(nome_programa)
            self.destroy() # Fecha a janela de "Limpeza Focada"
        else:
            pass

    def abrir_app_features(self, nome_programa):
        """
        Abre a tela 'Aplicativos e Recursos' do Windows, filtrando
        pelo nome do programa.
        """
        # Codifica o nome do programa para a URI (ex: "My App" -> "My%20App")
        nome_codificado = urllib.parse.quote(nome_programa)

        # Comando URI para abrir apps e filtrar (search)
        comando = f'start ms-settings:appsfeatures?search={nome_codificado}'

        try:
            # shell=True é necessário para o comando 'start'
            # check=True garante que o comando foi executado
            subprocess.run(comando, shell=True, check=True)
        except Exception as e:
            print(f"Erro ao abrir 'Aplicativos e Recursos': {e}")
            messagebox.showerror("Erro", "Não foi possível abrir as Configurações do Windows.")


    def selecionar_pasta_para_vazias(self):
        """Seleciona o diretório alvo."""
        pasta = filedialog.askdirectory(title="Selecione onde procurar pastas vazias")
        if pasta:
            self.pasta_vazias_alvo.set(pasta)

    def iniciar_escaneamento_vazias(self):
        pasta = self.pasta_vazias_alvo.get()
        if not os.path.isdir(pasta):
            messagebox.showerror("Erro", "Selecione uma pasta válida primeiro.")
            return

        self.btn_scan_vazias.config(state='disabled', text="Buscando...")
        self.loading_label.config(text=f"Varrendo pastas vazias em {os.path.basename(pasta)}...")

        # Inicia Thread
        threading.Thread(target=self.processar_busca_vazias, args=(pasta,), daemon=True).start()

    def processar_busca_vazias(self, pasta):
        # Chama o backend
        pastas_encontradas = limpeza.encontrar_pastas_vazias(pasta)

        # Volta para a GUI
        self.after(0, lambda: self.mostrar_resultado_vazias(pastas_encontradas))

    def mostrar_resultado_vazias(self, lista_pastas):
        # Verifica se janela existe
        if not self.winfo_exists(): return

        self.btn_scan_vazias.config(state='normal', text="Buscar Pastas Vazias")
        self.loading_label.config(text="")

        qtd = len(lista_pastas)
        if qtd == 0:
            messagebox.showinfo("Resultado", "Nenhuma pasta vazia encontrada.")
            return

        # ⭐️ MUDANÇA: Em vez de perguntar direto, abre a janela de visualização
        # Passamos 'self.iniciar_delecao_vazias' como callback
        EmptyFoldersViewer(self, lista_pastas, self.iniciar_delecao_vazias)

    def iniciar_delecao_vazias(self, lista_pastas):
        """Função auxiliar chamada pela janela de visualização para começar a thread."""
        self.loading_label.config(text="Removendo pastas...")
        threading.Thread(target=self.executar_delecao_vazias, args=(lista_pastas,), daemon=True).start()

    def executar_delecao_vazias(self, lista_pastas):
        removidas = limpeza.remover_pastas_vazias(lista_pastas)
        self.after(0, lambda: self.finalizar_delecao_vazias(removidas))

    def finalizar_delecao_vazias(self, qtd_removida):
        if not self.winfo_exists(): return

        self.loading_label.config(text="Concluído.")
        messagebox.showinfo("Sucesso", f"{qtd_removida} pastas vazias foram removidas.")

if __name__ == "__main__":
    app = ConfigScreen()
    app.mainloop()