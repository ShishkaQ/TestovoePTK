import re
import requests
import pandas as pd
from bs4 import BeautifulSoup


class TariffParser:

    BASE_URL = "https://www.rialcom.ru/internet_tariffs/"
    
    def __init__(self):
        self.session = requests.Session()
        self.soup = None
        self.tv_channel_map = {}
        

    def fetch_page(self):
        """Загружает и парсит HTML-страницу"""
        response = self.session.get(self.BASE_URL)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.text, "html.parser")
        return self.soup


    def parse_internet_tariffs(self, section_id, is_private=False):
        """Парсит интернет-тарифы для указанного раздела"""
        section = self.soup.find("div", id=section_id)
        if not section:
            return []
            
        tables = section.find_all("table")
        if not tables:
            return []
            
        # Первая таблица - интернет-тарифы
        table = tables[0]
        tariffs = []
        
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
                
            name = cols[0].get_text(strip=True)
            
            name = name.replace("**", "")
            
            fee_text = cols[1].get_text(strip=True)
            fee = int(re.sub(r"\D", "", fee_text)) if fee_text else 0
            
            # Обработка скорости
            speed_text = cols[3].get_text(strip=True)
            speed_match = re.search(r"(\d+)", speed_text)
            if speed_match:
                speed = int(speed_match.group(1)) // 1000
            else:
                speed = None
                
            tariffs.append({
                "Название тарифа": name,
                "Количество каналов": None,
                "Скорость доступа": speed,
                "Абонентская плата": fee
            })
        
        return tariffs
    
        
    def parse_tv_tariffs(self, section_id, is_private=False):
        """Парсит комбо-тарифы (интернет+ТВ) для указанного раздела"""
        section = self.soup.find("div", id=section_id)
        if not section:
            return []
            
        tables = section.find_all("table")
        if len(tables) < 2:
            return []
            
        # Вторая таблица - TV-тарифы
        table = tables[1]
        tariffs = []
        headers = []
        
        # Извлекаем заголовки столбцов
        header_row = table.find("tr")
        if header_row:
            for th in header_row.find_all("th")[1:]:
                header_text = th.get_text(strip=True)
                # Извлекаем скорость из заголовка
                speed_match = re.search(r"(\d+)", header_text)
                headers.append(int(speed_match.group(1)) if speed_match else None)
        
        # Обработка строк с тарифами
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if not cols:
                continue
                
            # Извлечение названия тарифа и количества каналов
            name_cell = cols[0].get_text(strip=True)
            # Удаляем ** из названия тарифа
            name_cell = name_cell.replace("**", "")
            
            channels_match = re.search(r"\((\d+) канал", name_cell)
            channels = int(channels_match.group(1)) if channels_match else None
            base_name = re.sub(r"\(\d+ канал.*\)", "", name_cell).strip()
            
            # Сохраняем количество каналов для частных домов
            if not is_private:
                self.tv_channel_map[base_name] = channels
            
            # Обработка ценовых ячеек
            for idx, cell in enumerate(cols[1:]):
                if idx >= len(headers) or not headers[idx]:
                    continue
                    
                fee_text = cell.get_text(strip=True)
                if not fee_text:
                    continue
                    
                fee = int(re.sub(r"\D", "", fee_text))
                speed = headers[idx]
                
                # Формирование названия тарифа
                if is_private:
                    
                    tariff_name = f"{base_name} + РиалКом Интернет {speed} + ТВ_ч"
                else:

                    tariff_name = f"{base_name} + РиалКом Интернет {speed} + ТВ"
                
                tariffs.append({
                    "Название тарифа": tariff_name,
                    "Количество каналов": channels if not is_private else self.tv_channel_map.get(base_name),
                    "Скорость доступа": speed,
                    "Абонентская плата": fee
                })
        
        return tariffs
    
        
    def parse_all(self):
        """Парсит все типы тарифов"""
        self.fetch_page()
        
        results = []

        results.extend(self.parse_internet_tariffs("collapse1"))
        
        results.extend(self.parse_tv_tariffs("collapse1"))
        
        private_internet = self.parse_internet_tariffs("collapse2", is_private=True)
        results.extend(private_internet)
        
        private_tv_tariffs = self.parse_tv_tariffs("collapse2", is_private=True)
        results.extend(private_tv_tariffs)
        
        return results
    
        
    def to_excel(self, data, filename="tariffs.xlsx"):
        """Сохраняет данные в Excel-файл с помощью pandas"""
        df = pd.DataFrame(data)
        
        df["Количество каналов"] = df["Количество каналов"].apply(lambda x: 'null' if pd.isna(x) or x is None else x)
        
        df.to_excel(filename, index=False)
        return filename
    