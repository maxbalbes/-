import requests
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import json
import os
from datetime import datetime

class ProxyGenerator:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.sources = [
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://www.proxy-list.download/api/v1/get?type=https",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
        ]
        
    def generate_random_ip(self):
        """Генерация случайного IP адреса"""
        return ".".join(str(random.randint(1, 255)) for _ in range(4))
    
    def generate_random_port(self):
        """Генерация случайного порта"""
        return random.randint(1000, 65535)
    
    def create_fake_proxy(self, protocol='http'):
        """Создание фейкового прокси"""
        ip = self.generate_random_ip()
        port = self.generate_random_port()
        return {
            'ip': ip,
            'port': port,
            'protocol': protocol,
            'country': random.choice(['US', 'RU', 'DE', 'FR', 'UK', 'CA', 'JP', 'CN']),
            'anonymity': random.choice(['transparent', 'anonymous', 'elite']),
            'speed': random.randint(100, 5000),
            'uptime': random.randint(50, 100),
            'last_checked': datetime.now().isoformat()
        }
    
    def generate_fake_proxies(self, count=100):
        """Генерация списка фейковых прокси"""
        protocols = ['http', 'https', 'socks4', 'socks5']
        fake_proxies = []
        
        for i in range(count):
            protocol = random.choice(protocols)
            proxy = self.create_fake_proxy(protocol)
            fake_proxies.append(proxy)
            
        return fake_proxies
    
    def fetch_proxies_from_sources(self):
        """Получение прокси из онлайн источников"""
        all_proxies = []
        
        for source in self.sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    for line in lines:
                        if ':' in line:
                            ip, port = line.strip().split(':')
                            proxy = {
                                'ip': ip,
                                'port': int(port),
                                'protocol': 'http',
                                'source': source,
                                'last_checked': datetime.now().isoformat()
                            }
                            all_proxies.append(proxy)
                time.sleep(1)  # Задержка между запросами
            except Exception as e:
                print(f"Ошибка при получении прокси из {source}: {e}")
                
        return all_proxies
    
    def check_proxy(self, proxy, timeout=5):
        """Проверка работоспособности прокси"""
        try:
            proxy_url = f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # Тестируем подключение к Google
            start_time = time.time()
            response = requests.get(
                'http://www.google.com', 
                proxies=proxies, 
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                proxy['response_time'] = round((end_time - start_time) * 1000, 2)
                proxy['working'] = True
                proxy['last_checked'] = datetime.now().isoformat()
                return proxy
        except Exception as e:
            pass
            
        proxy['working'] = False
        return proxy
    
    def validate_proxies(self, proxies, max_workers=20):
        """Многопоточная проверка прокси"""
        working_proxies = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(self.check_proxy, proxies)
            
            for result in results:
                if result['working']:
                    working_proxies.append(result)
                    print(f"✓ Рабочий прокси: {result['ip']}:{result['port']} - {result['response_time']}ms")
                else:
                    print(f"✗ Не рабочий: {result['ip']}:{result['port']}")
                    
        return working_proxies
    
    def save_proxies(self, proxies, filename="proxies.json"):
        """Сохранение прокси в файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(proxies, f, indent=2, ensure_ascii=False)
        print(f"Прокси сохранены в {filename}")
    
    def load_proxies(self, filename="proxies.json"):
        """Загрузка прокси из файла"""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def export_to_txt(self, proxies, filename="proxies.txt"):
        """Экспорт прокси в текстовый файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            for proxy in proxies:
                f.write(f"{proxy['ip']}:{proxy['port']}\n")
        print(f"Прокси экспортированы в {filename}")
    
    def get_proxy_string(self, proxy):
        """Получение строки прокси в формате ip:port"""
        return f"{proxy['ip']}:{proxy['port']}"
    
    def filter_proxies(self, proxies, **filters):
        """Фильтрация прокси по параметрам"""
        filtered = proxies
        
        if 'protocol' in filters:
            filtered = [p for p in filtered if p.get('protocol') == filters['protocol']]
        
        if 'country' in filters:
            filtered = [p for p in filtered if p.get('country') == filters['country']]
        
        if 'min_speed' in filters:
            filtered = [p for p in filtered if p.get('speed', 0) >= filters['min_speed']]
        
        if 'anonymity' in filters:
            filtered = [p for p in filtered if p.get('anonymity') == filters['anonymity']]
        
        return filtered

class AdvancedProxyGenerator(ProxyGenerator):
    def __init__(self):
        super().__init__()
        self.rotating_proxies = []
        
    def create_rotating_proxy_list(self, base_proxies, rotation_interval=60):
        """Создание ротирующего списка прокси"""
        self.rotating_proxies = base_proxies.copy()
        self.rotation_interval = rotation_interval
        
        # Запуск ротации в отдельном потоке
        rotation_thread = threading.Thread(target=self._rotate_proxies)
        rotation_thread.daemon = True
        rotation_thread.start()
    
    def _rotate_proxies(self):
        """Ротация прокси в фоновом режиме"""
        while True:
            time.sleep(self.rotation_interval)
            if self.rotating_proxies:
                # Перемешиваем список прокси
                random.shuffle(self.rotating_proxies)
                print(f"Прокси ротированы. Доступно: {len(self.rotating_proxies)}")
    
    def get_rotating_proxy(self):
        """Получение случайного прокси из ротирующего списка"""
        if self.rotating_proxies:
            return random.choice(self.rotating_proxies)
        return None
    
    def generate_proxy_with_authentication(self, count=10):
        """Генерация прокси с авторизацией"""
        auth_proxies = []
        
        for i in range(count):
            proxy = self.create_fake_proxy()
            proxy['username'] = f'user_{random.randint(1000, 9999)}'
            proxy['password'] = f'pass_{random.randint(10000, 99999)}'
            proxy['auth_required'] = True
            auth_proxies.append(proxy)
            
        return auth_proxies

def main():
    generator = AdvancedProxyGenerator()
    
    while True:
        print("\n" + "="*50)
        print("          ГЕНЕРАТОР ПРОКСИ-СЕРВЕРОВ")
        print("="*50)
        print("1. Сгенерировать фейковые прокси")
        print("2. Загрузить прокси из онлайн источников")
        print("3. Проверить работоспособность прокси")
        print("4. Сохранить прокси в файл")
        print("5. Загрузить прокси из файла")
        print("6. Экспорт в текстовый формат")
        print("7. Фильтровать прокси")
        print("8. Создать ротирующие прокси")
        print("9. Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == '1':
            count = int(input("Количество прокси для генерации: "))
            fake_proxies = generator.generate_fake_proxies(count)
            generator.proxies.extend(fake_proxies)
            print(f"Сгенерировано {len(fake_proxies)} фейковых прокси")
            
        elif choice == '2':
            print("Загрузка прокси из онлайн источников...")
            online_proxies = generator.fetch_proxies_from_sources()
            generator.proxies.extend(online_proxies)
            print(f"Загружено {len(online_proxies)} прокси из онлайн источников")
            
        elif choice == '3':
            if not generator.proxies:
                print("Сначала загрузите или сгенерируйте прокси!")
                continue
                
            print("Проверка работоспособности прокси...")
            workers = int(input("Количество потоков для проверки (рекомендуется 10-20): "))
            generator.working_proxies = generator.validate_proxies(generator.proxies, workers)
            print(f"Найдено {len(generator.working_proxies)} рабочих прокси")
            
        elif choice == '4':
            if generator.working_proxies:
                generator.save_proxies(generator.working_proxies)
            else:
                generator.save_proxies(generator.proxies)
                
        elif choice == '5':
            filename = input("Имя файла (по умолчанию proxies.json): ") or "proxies.json"
            loaded_proxies = generator.load_proxies(filename)
            if loaded_proxies:
                generator.proxies = loaded_proxies
                print(f"Загружено {len(loaded_proxies)} прокси")
            else:
                print("Файл не найден или пуст")
                
        elif choice == '6':
            if generator.working_proxies:
                generator.export_to_txt(generator.working_proxies)
            else:
                generator.export_to_txt(generator.proxies)
                
        elif choice == '7':
            if not generator.proxies:
                print("Нет прокси для фильтрации!")
                continue
                
            print("\nФильтрация прокси:")
            print("Доступные параметры: protocol, country, min_speed, anonymity")
            param = input("Параметр для фильтрации: ")
            value = input("Значение: ")
            
            filters = {param: value}
            if param == 'min_speed':
                filters[param] = int(value)
                
            filtered = generator.filter_proxies(generator.proxies, **filters)
            print(f"Найдено {len(filtered)} прокси по фильтру")
            
            # Показать первые 10 результатов
            for i, proxy in enumerate(filtered[:10]):
                print(f"{i+1}. {proxy['ip']}:{proxy['port']} - {proxy.get('protocol', 'http')}")
                
        elif choice == '8':
            if not generator.working_proxies:
                print("Сначала найдите рабочие прокси!")
                continue
                
            interval = int(input("Интервал ротации в секундах: "))
            generator.create_rotating_proxy_list(generator.working_proxies, interval)
            print(f"Создан ротирующий список из {len(generator.working_proxies)} прокси")
            
            # Демонстрация ротации
            for i in range(5):
                proxy = generator.get_rotating_proxy()
                if proxy:
                    print(f"Прокси {i+1}: {proxy['ip']}:{proxy['port']}")
                time.sleep(1)
                
        elif choice == '9':
            print("Выход...")
            break
            
        else:
            print("Неверный выбор!")

# Пример использования в коде
def example_usage():
    """Пример использования генератора прокси"""
    generator = ProxyGenerator()
    
    # Генерация фейковых прокси
    fake_proxies = generator.generate_fake_proxies(50)
    print(f"Сгенерировано {len(fake_proxies)} фейковых прокси")
    
    # Загрузка реальных прокси
    real_proxies = generator.fetch_proxies_from_sources()
    print(f"Загружено {len(real_proxies)} реальных прокси")
    
    # Объединение списков
    all_proxies = fake_proxies + real_proxies
    
    # Проверка работоспособности
    working_proxies = generator.validate_proxies(all_proxies[:100])  # Проверяем первые 100
    
    # Сохранение
    generator.save_proxies(working_proxies)
    
    # Использование прокси в requests
    if working_proxies:
        proxy = working_proxies[0]
        proxy_str = generator.get_proxy_string(proxy)
        
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': f'http://{proxy_str}', 'https': f'http://{proxy_str}'},
                timeout=10
            )
            print(f"Ответ через прокси: {response.json()}")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    # Запуск интерактивного меню
    main()
    
    # Или пример использования
    # example_usage()