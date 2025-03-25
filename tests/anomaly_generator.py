import threading
import requests
import time
import random
import math
import socket

TARGETS = [
    ('localhost', 8080),   # server
    ('localhost', 8081),   # adminer
    ('localhost', 8083),   # file-api
    ('localhost', 8090),   # anomaly detector (запрос на себя)
    ('localhost', 27017),  # mongo
    ('localhost', 5432),   # postgres
]

# 🚀 Имитация нагрузки на CPU
def cpu_stress():
    while True:
        [math.sqrt(random.randint(1, 10000)) for _ in range(10000)]

# 🚀 Брутальная атака на REST и TCP порты
def port_stress():
    while True:
        for host, port in TARGETS:
            try:
                # TCP ping
                with socket.create_connection((host, port), timeout=0.5):
                    pass
            except:
                pass

            # Если HTTP-порт - шлём запрос
            if port in (8080, 8081, 8083, 8090):
                try:
                    requests.get(f"http://{host}:{port}", timeout=0.5)
                except:
                    pass
        time.sleep(0.01)  # Регулируем агрессивность

if __name__ == "__main__":
    print("🚨 Аномалия запущена — нагрузка и стуки по портам")
    # Стартуем нагрузку на CPU
    for _ in range(7):  # 4 ядра грузим
        threading.Thread(target=cpu_stress, daemon=True).start()

    # Стартуем сетевую атаку на стек
    threading.Thread(target=port_stress, daemon=True).start()

    while True:
        time.sleep(0.01)
