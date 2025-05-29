from parser import TariffParser

def main():
    parser = TariffParser()
    tariffs = parser.parse_all()
    print(f"Спаршено тарифов: {len(tariffs)}")
    parser.to_excel(tariffs)
    print("Файл сохранен как tariffs.xlsx")

if __name__ == "__main__":
    main()