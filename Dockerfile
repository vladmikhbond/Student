 
# Базовий образ з Python 3.12 
FROM python:3.12-slim

# Копіюємо requirements.txt у контейнер 
COPY requirements.txt /tmp/requirements.txt
COPY run.py /run.py
COPY app /app

# Встановлюємо Python-залежності
RUN pip install --no-cache-dir -r /tmp/requirements.txt
                                 
# Відкриваємо порт
EXPOSE 7004

CMD ["python", "run.py"]