
FROM ubuntu:latest

# Running as root (security issue)
USER root

# Installing packages without specific versions
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    wget

# Copying secrets into image (bad practice)
COPY secret_key.txt /app/

# Setting weak permissions
RUN chmod 777 /app

# Exposing unnecessary ports
EXPOSE 22 80 443 8080 9000

# Running with elevated privileges
CMD ["python3", "app.py"]
