# Start with the official Python image (replace python:3.9-slim with the version you need)
FROM python:3.6

# Install required packages (Apache,PHP, SSH, locales, crontab, system logs)
RUN apt-get update && apt-get install -y \
    apache2 php libapache2-mod-php \
    openssh-server locales vim cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the system locale to Greek (UTF-8)
RUN sed -i '/el_GR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen el_GR.UTF-8
ENV LANG el_GR.UTF-8
ENV LANGUAGE el_GR:el
ENV LC_ALL el_GR.UTF-8

# Ensure vi uses UTF-8
RUN echo "set encoding=utf-8" >> /etc/vim/vimrc


# Create directory and add files for /opt/python/scalping-bot
RUN mkdir -p /opt/python/scalping-bot/ && \
    chown -R root:root /opt/python/scalping-bot && \
    chmod -R 755 /opt/python/scalping-bot

# Create logs directory inside /opt/python/scalping-bot
RUN mkdir -p /opt/python/scalping-bot/logs

# Copy the files to the directory (assuming they are in the local build context)
COPY scalper.py /opt/python/scalping-bot/
RUN chmod 755 /opt/python/scalping-bot/scalper.py

# Copy requirements.txt to the container
COPY requirements.txt /opt/python/scalping-bot/requirements.txt
RUN chmod 644 /opt/python/scalping-bot/requirements.txt

# Install Python libraries from requirements.txt
RUN pip install --no-cache-dir -r /opt/python/scalping-bot/requirements.txt


# Generate SSH host keys
RUN mkdir /var/run/sshd && \
    ssh-keygen -A

# Set root password
RUN echo 'root:6834734' | chpasswd

# Expose necessary ports (SSH)
EXPOSE 22

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Start services via entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
