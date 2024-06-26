import requests
import json
import os
import holidays
import urllib3
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import BOTH, CENTER, messagebox
from PIL import Image, ImageTk
from calendar import monthrange
from datetime import datetime, timezone, timedelta, date
from dotenv import load_dotenv
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
api_key = os.getenv('API_KEY')
application_key = os.getenv('APPLICATION_KEY')

url = 'https://api.datadoghq.com/api/v1/query'

headers = {
    'Content-Type': 'application/json',
    'DD-API-KEY': api_key,
    'DD-APPLICATION-KEY': application_key
}
with open('querys/dashboard_queries_requisicoes.json', 'r') as file:
    dashboard_queries_req_data = json.load(file)
with open('querys/dashboard_queries_degradacao.json', 'r') as file:
    dashboard_queries_deg_data = json.load(file)
with open('querys/dashboard_queries_indisponibilidade.json', 'r') as file:
    dashboard_queries_ind_data = json.load(file)

dashboard_queries_requisicoes = dashboard_queries_req_data['requisicoes']
dashboard_queries_degradacao = dashboard_queries_deg_data['degradacao']
dashboard_queries_indisponibilidade = dashboard_queries_ind_data['indisponibilidade']
def run_query(query, from_time, to_time):
    params = {
        'query': query,
        'from': from_time,
        'to': to_time
    }
    response = requests.get(url, headers=headers, params=params, verify= False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Erro ao executar a consulta: {response.status_code}')
        print(response.text)
        return None

def sum_points(series):
    if series and 'pointlist' in series[0]:
        return sum(point[1] for point in series[0]['pointlist'])
    else:
        return 0

def to_timestamp(year, month, day, hour=0, minute=0, tz_offset=-3):
    dt = datetime(year, month, day, hour, minute) - timedelta(hours=tz_offset)
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


def is_weekend(year, month, day):
    return datetime(year, month, day).weekday() >= 5

br_holidays = holidays.Brazil()

def is_holiday(year, month, day):
    return date(year, month, day) in br_holidays

sistemas = {
    "TOP SAÚDE": [
        'Autorizações', 'Contas Médicas', 'Integrações-Internas', 'Integrações-Portais', 'Relatórios', 'Integrações-TISS'
    ],
    "E-PREV": [
        'Site Administrativo', 'Serviços WCF', 'Portal do Corretor', 'API Corretora Digital', 'Administrativo – Chamadas aos serviços WCF', 
        'Portal do Corretor – Chamadas aos serviços WCF', 'Serviços – Chamadas a serviços externos', 'API Corretora Digital – Chamadas aos serviços WCF', 
        'Previdência PF', 'Financeiro PF'
    ],
    "DROOLS": [
        'Previdência', '(ANS) Saúde', '(ANS) Odonto', 'DEO - Seguro Responsabilidade Civil', 'Empresarial', 'Empresarial - Legado', 
        'Residencial', 'Residencial - Legado', 'RCPSI - Seguro Responsabilidade Civil Individual', 'RCPSI - Seguro Responsabilidade Civil Individual - Legado', 
        'RCPSO - Seguro Responsabilidade Civil Coletivo - Legado'
    ],
    "UNISERVICES": [
        'API SAUDE', 'API ODONTO', 'API SIEBEL', 'API JOKER', 'API VIDA', 'API PREV', 'API RE', 'API BASE21', 'API GEM'
    ],
    "CALCULE+": [
        'Cotação', 'Área Cliente', 'Autenticação', 'Layouts', 'Proposta', 'Transmissão'
    ],
    "PORTAL DA SEGUROS": [
        'Autenticação em Sistemas (SSO-PRD)', 'Token URL do Frame', 'Token URL Sinistro online Vida', 'Criação/Atualização de Estipulante', 
        'Criação/Atualização de corretor', 'Gerar PDF Dirf', 'Gerar Token Core', 'Token URL do Sinistro Online Patrimonial'
    ],
    "PORTAL INST / PF / SUPER APP": [
        'Dados Segurados Odonto', 'Dados Segurados Previdencia', 'Dados Segurados Vida', 'Dados Segurados RE', 'Dados Segurados Saúde'
    ],
    "SIEBEL": [
        'Protocolo ANS'
    ],
    "E-BAO": [
        'EMPRE', 'GERAL', 'RCP', 'RESID', 'POST /produto/apolice'
    ],
    "TOP DENTAL": [
        'Portal Empresa', 'Portal Segurado', 'Portal Dentista', 'Top Dental', 'movimentacao-cadastral', 'token-corporativo'
    ]
}

cancel_processing = False

def process_service_data(year, month, days_to_process):
    services_data = {}

    _, last_day = monthrange(year, month)
    days_to_process = min(days_to_process, last_day)
    
    service_names = ['Autorizações', 'Contas Médicas', 'Integrações-Internas', 'Integrações-Portais', 'Relatórios', 'Integrações-TISS', 'Site Administrativo', 'Serviços WCF', 'Portal do Corretor',
                        'API Corretora Digital', 'Administrativo – Chamadas aos serviços WCF', 'Portal do Corretor – Chamadas aos serviços WCF', 'Serviços – Chamadas a serviços externos',
                        'API Corretora Digital – Chamadas aos serviços WCF', 'Previdência PF', 'Financeiro PF','Previdência', '(ANS) Saúde', '(ANS) Odonto',
                        'DEO - Seguro Responsabilidade Civil', 'Empresarial', 'Empresarial - Legado', 'Residencial', 'Residencial - Legado', 'RCPSI - Seguro Responsabilidade Civil Individual',
                        'RCPSI - Seguro Responsabilidade Civil Individual - Legado', 'RCPSO - Seguro Responsabilidade Civil Coletivo - Legado', 'API SAUDE',
                        'API ODONTO', 'API SIEBEL', 'API JOKER', 'API VIDA', 'API PREV', 'API RE', 'API BASE21', 'API GEM', 'Cotação', 'Área Cliente', 'Autenticação', 'Layouts', 'Proposta', 'Transmissão',
                        'Autenticação em Sistemas (SSO-PRD)', 'Token URL do Frame', 'Token URL Sinistro online Vida', 'Criação/Atualização de Estipulante', 'Criação/Atualização de corretor', 'Gerar PDF Dirf',
                        'Gerar Token Core', 'Token URL do Sinistro Online Patrimonial', 'Dados Segurados Odonto', 'Dados Segurados Previdencia', 'Dados Segurados Vida', 'Dados Segurados RE',
                        'Dados Segurados Saúde', 'Protocolo ANS', 'EMPRE', 'GERAL', 'RCP', 'RESID', 'POST /produto/apolice', 'Portal Empresa', 'Portal Segurado',
                        'Portal Dentista', 'Top Dental', 'movimentacao-cadastral', 'token-corporativo']
    for service_name in service_names:
        services_data[service_name] = {
            'requisicoes': 0,
            'degradacao': 0,
            'indisponibilidade': 0,
            'porcentagem_degradacao': 0,
            'porcentagem_indisponibilidade': 0,
            'erros_totais': 0,
            'SLA (5xx)': 0
        }
    total_days = days_to_process
    processed_days = 0
    for day in range(1, days_to_process + 1):
        if is_weekend(year, month, day) or is_holiday(year, month, day):
            continue
        
        from_time = to_timestamp(year, month, day, 7)
        to_time = to_timestamp(year, month, day, 19)

        update_status(f"Processando dia {day}...")

        for service_index, service_name in enumerate(service_names):
            for data_type in ['requisicoes', 'degradacao', 'indisponibilidade']:
                queries_list = globals()[f'dashboard_queries_{data_type}']
                query_info = globals()[f'dashboard_queries_{data_type}'][service_index]
                if service_index < len(queries_list):
                    query_info = queries_list[service_index]
                    for request in query_info['requests']:
                        for query_detail in request['queries']:
                            query = query_detail['query']
                            result = run_query(query, from_time, to_time)
                            if cancel_processing:
                                return
                            if result is not None and 'series' in result:
                                query_total = sum_points(result['series'])
                                services_data[service_name][data_type] += query_total
                else:
                    print(f"Não há consulta definida para {service_name} em {data_type}.")
        processed_days += 1
        update_status(f"Processamento de {processed_days}/{total_days} dias concluído.")
        update_progress((processed_days / total_days) * 100)
                    
    for service_name in service_names:
        erros_totais = services_data[service_name]['degradacao'] + services_data[service_name]['indisponibilidade']
        services_data[service_name]['erros_totais'] = erros_totais

        if services_data[service_name]['requisicoes'] > 0:
            porcentagem_indisponibilidade = (services_data[service_name]['indisponibilidade'] / services_data[service_name]['requisicoes']) * 100
            services_data[service_name]['porcentagem_degradacao'] = f"{round((services_data[service_name]['degradacao'] / services_data[service_name]['requisicoes']) * 100, 2)}%"
            services_data[service_name]['porcentagem_indisponibilidade'] = f"{round((services_data[service_name]['indisponibilidade'] / services_data[service_name]['requisicoes']) * 100, 2)}%"
            services_data[service_name]['SLA (5xx)'] = f"{round(100 - porcentagem_indisponibilidade, 2)}%"
        else:
            services_data[service_name]['porcentagem_degradacao'] = "0.00%"
            services_data[service_name]['porcentagem_indisponibilidade'] = "0.00%"
            services_data[service_name]['SLA (5xx)'] = "100.00%"

    sistemas_sla_data = {}
    for sistema, servicos in sistemas.items():
        slas = []
        for servico in servicos:
            if servico in services_data:
                sla_value = services_data[servico]['SLA (5xx)'].rstrip('%')
                slas.append(float(sla_value))
        if slas:
            sistemas_sla_data[sistema] = sum(slas) / len(slas) 
        else:
            sistemas_sla_data[sistema] = 100.0 

    for sistema, sla_total in sistemas_sla_data.items():
        for servico in sistemas[sistema]:
            services_data[servico]['SLA_Sistema'] = f"{round(sla_total, 2)}%"
    
    return services_data

def save_data_to_json(all_services_data, sistemas, file_name):
    if not os.path.exists('data'):
        os.makedirs('data')

    file_path = os.path.join('data', file_name)

    sistemas_data = {sistema: {} for sistema in sistemas}
    for sistema, servicos in sistemas.items():
        sistemas_data[sistema] = {servico: {k: v for k, v in all_services_data[servico].items() if k != 'SLA_Sistema'} for servico in servicos if servico in all_services_data}

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(sistemas_data, file, ensure_ascii=False, indent=4)
        print(f"Os dados de serviço foram salvos com sucesso em {file_path}")
    
    sistemas_data_with_sla = {}
    for sistema in sistemas:
        sla_sistema_values = [float(all_services_data[servico]['SLA_Sistema'].rstrip('%')) for servico in sistemas[sistema] if servico in all_services_data]
        if sla_sistema_values:
            sla_total_sistema = sum(sla_sistema_values) / len(sla_sistema_values)
            sistemas_data_with_sla[sistema] = {'SLA_Total': f"{round(sla_total_sistema, 2)}%", 'Servicos': sistemas_data[sistema]}
        else:
            sistemas_data_with_sla[sistema] = {'SLA_Total': "100.00%", 'Servicos': sistemas_data[sistema]}

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(sistemas_data_with_sla, file, ensure_ascii=False, indent=4)
        print(f"Os dados de sistemas foram salvos com sucesso em {file_path}")

def process_and_save_data(year, month):
    global cancel_processing
    update_status("Processando dados...")
    _, days_to_process = monthrange(year, month) 
    all_services_monthly_data = process_service_data(year, month, days_to_process)
    if not cancel_processing:
        file_name = f'service_data_{year}_{month:02d}.json'
        save_data_to_json(all_services_monthly_data, sistemas, file_name)
        update_status("Processamento concluído com sucesso!")
        messagebox.showinfo("Concluído", "Processamento concluído com sucesso!")
    else:
        messagebox.showinfo("Cancelado", "Processamento cancelado pelo usuário.")
        update_status("")

def clear_status_after_cancel():
    global root
    time.sleep(2) 
    if cancel_processing:
        update_status("")

def update_progress(value):
    global progress, progress_label
    progress['value'] = value
    percentage = (value / progress['maximum']) * 100
    progress_label.config(text=f"{percentage:.2f}%")
    root.update_idletasks()
    
def update_status(message):
    global root, status_label
    status_label.config(text=message)
    root.update_idletasks()

def clear_status_after_cancel():
    global root
    time.sleep(2)
    if cancel_processing:
        update_status("")

def main():
    def start_processing():
        global cancel_processing
        cancel_processing = False
        try:
            year = year_entry.get()
            month = month_entry.get()

            if not year.isdigit() or len(year) != 4:
                messagebox.showerror("Erro", "Por favor, insira um ano válido com 4 dígitos.")
                return

            if not month.isdigit() or not (1 <= int(month) <= 12):
                messagebox.showerror("Erro", "Por favor, insira um mês válido (1-12).")
                return

            year = int(year)
            month = int(month)

            if year >= 2023:
                if month >= 1 and month <= 12:
                    update_status("Iniciando processamento...")

                    threading.Thread(target=process_and_save_data, args=(year, month)).start()
                else:
                    messagebox.showerror("Erro", "Mês inválido.")
            else:
                messagebox.showerror("Erro", "Não existem dados anteriores a 2023.")
        except ValueError:
            messagebox.showerror("Erro", "Ano ou mês inválido.")

    def cancel_processing_function():
        global cancel_processing
        cancel_processing = True
        update_status("Cancelando o processamento...")
        threading.Thread(target=clear_status_after_cancel).start()

    def rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            (x1 + radius, y1),
            (x2 - radius, y1),
            (x2, y1),
            (x2, y1 + radius),
            (x2, y2 - radius),
            (x2, y2),
            (x2 - radius, y2),
            (x1 + radius, y2),
            (x1, y2),
            (x1, y2 - radius),
            (x1, y1 + radius),
            (x1, y1)
        ]
        canvas.create_arc(x1, y1, x1 + 2 * radius, y1 + 2 * radius, start=90, extent=90, style="arc", **kwargs)
        canvas.create_arc(x2 - 2 * radius, y1, x2, y1 + 2 * radius, start=0, extent=90, style="arc", **kwargs)
        canvas.create_arc(x2 - 2 * radius, y2 - 2 * radius, x2, y2, start=270, extent=90, style="arc", **kwargs)
        canvas.create_arc(x1, y2 - 2 * radius, x1 + 2 * radius, y2, start=180, extent=90, style="arc", **kwargs)

        canvas.create_line(points[0], points[1], **kwargs)
        canvas.create_line(points[3], points[4], **kwargs)
        canvas.create_line(points[6], points[7], **kwargs)
        canvas.create_line(points[9], points[10], **kwargs)

    global root, progress, progress_label, status_label
    root = ttk.Window(themename="morph")
    root.title("Consulta de Dados")
    root.geometry("800x600")

    logo_image = Image.open("logo-seguros.png")
    logo_image = logo_image.resize((150, 80)) 
    logo_photo = ImageTk.PhotoImage(logo_image)

    canvas = ttk.Canvas(root, width=800, height=600)
    canvas.pack(expand=True, fill=BOTH)
    canvas.create_image(400, 75, image=logo_photo, anchor=CENTER) 
    rounded_rectangle(canvas, 200, 25, 600, 575, 20, fill="navy", width=3) 

    frame_content = ttk.Frame(canvas, padding=10)
    frame_content.place(relx=0.5, rely=0.5, anchor=CENTER)

    inner_frame = ttk.Frame(canvas)
    canvas.create_window(400, 350, window=inner_frame, anchor=CENTER) 

    year_label = ttk.Label(inner_frame, text="ANO:", style='TLabel')
    year_label.pack(pady=5, anchor=CENTER)

    year_entry = ttk.Entry(inner_frame, width=15, style='TEntry')
    year_entry.pack(pady=5, anchor=CENTER)

    month_label = ttk.Label(inner_frame, text="MÊS (1-12):", style='TLabel')
    month_label.pack(pady=5, anchor=CENTER)

    month_entry = ttk.Entry(inner_frame, width=15, style='TEntry')
    month_entry.pack(pady=5, anchor=CENTER)
    process_button = ttk.Button(
            inner_frame, 
            text="PROCESSAR", 
            command=start_processing, 
            bootstyle=(OUTLINE, SUCCESS), 
            width=15, 
            padding=(20, 5)
        )
    process_button.pack(pady=20, anchor=CENTER)
    cancel_button = ttk.Button(
            inner_frame, 
            text="PARAR", 
            command=cancel_processing_function, 
            bootstyle=(OUTLINE, DANGER), 
            width=15, 
            padding=(20, 5)
        )
    cancel_button.pack(pady=5, anchor=CENTER)

    progress = ttk.Progressbar(inner_frame, mode='determinate', bootstyle="info-striped", length=200)
    progress.pack(pady=10, anchor=CENTER)

    progress_label = ttk.Label(inner_frame, text="0%", style='TLabel')
    progress_label.pack(pady=5, anchor=CENTER)

    status_label = ttk.Label(inner_frame, text="", style='TLabel')
    status_label.pack(pady=10, anchor=CENTER)

    style = ttk.Style()
    style.configure('TButton', font=('Helvetica', 9, 'bold'), padding=10)
    style.configure('TLabel', font=('Helvetica', 9, 'bold'), foreground='navy')
    style.configure('TEntry', font=('Helvetica', 9, 'bold'))

    root.mainloop()

if __name__ == "__main__":
    main()