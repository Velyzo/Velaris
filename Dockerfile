FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80
CMD ["sh", "-c", "python bot.py --TOKEN=$TOKEN"]
