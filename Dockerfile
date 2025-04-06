FROM python:3.10

WORKDIR /app

# required packages
RUN pip install neo4j
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# make the wait-for-it script executable
COPY setup_scripts/initial_script.sh /initial_script.sh
RUN chmod +x /initial_script.sh

COPY data/products.json .
COPY data/co_occurrences.xlsx .
COPY setup_scripts/load_products_new.py .

# when the container starts, wait for neo4j:7687 and then run the script.
CMD ["/bin/sh", "-c", "/initial_script.sh neo4j:7687 -- python load_products_new.py"]
