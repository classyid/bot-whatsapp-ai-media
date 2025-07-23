## 🚀 Deployment Guide

### **Option 1: VPS Deployment (Recommended)**

#### 1. **Server Requirements**
```bash
# Minimum specs:
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB SSD
- OS: Ubuntu 20.04+ or CentOS 8+
- Bandwidth: Unlimited/High
```

#### 2. **System Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3 python3-pip python3-venv -y

# Install system dependencies
sudo apt install ffmpeg wget curl git -y

# Install yt-dlp (latest version)
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp
```

#### 3. **Project Setup**
```bash
# Create project directory
mkdir whatsapp-ai-bot
cd whatsapp-ai-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << EOF
neonize==0.1.0
aiohttp>=3.8.0
yt-dlp>=2023.12.30
asyncio
thundra-io  # optional
EOF

# Install dependencies
pip install -r requirements.txt
```

#### 4. **Configuration**
```bash
# Create config file
cat > config.py << EOF
import os

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-api-key-here')
GEMINI_MODEL = "gemini-2.0-flash"

# Bot Configuration
MAX_FILE_SIZE_MB = 100
CLEANUP_INTERVAL_HOURS = 24
DOWNLOAD_DIR = "downloads"
TEMP_DIR = "temp_media"

# WhatsApp Configuration
DB_PATH = "db.sqlite3"
EOF

# Update main script to use config
# Replace hardcoded API key with:
# from config import GEMINI_API_KEY
```

#### 5. **Environment Variables**
```bash
# Create .env file
cat > .env << EOF
GEMINI_API_KEY=your-actual-gemini-api-key
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

# Load environment
echo "source .env" >> ~/.bashrc
```

#### 6. **Service Setup (Systemd)**
```bash
# Create systemd service
sudo cat > /etc/systemd/system/whatsapp-ai-bot.service << EOF
[Unit]
Description=WhatsApp AI Bot
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/whatsapp-ai-bot
Environment=PATH=/home/ubuntu/whatsapp-ai-bot/venv/bin
Environment=GEMINI_API_KEY=your-api-key
ExecStart=/home/ubuntu/whatsapp-ai-bot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable whatsapp-ai-bot
sudo systemctl start whatsapp-ai-bot
```

#### 7. **Monitoring & Logging**
```bash
# View logs
sudo journalctl -u whatsapp-ai-bot -f

# Check status
sudo systemctl status whatsapp-ai-bot

# Restart service
sudo systemctl restart whatsapp-ai-bot
```

### **Option 2: Docker Deployment**

#### 1. **Dockerfile**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p downloads temp_media

# Run application
CMD ["python", "main.py"]
```

#### 2. **Docker Compose**
```yaml
version: '3.8'

services:
  whatsapp-ai-bot:
    build: .
    container_name: whatsapp-bot
    restart: unless-stopped
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./downloads:/app/downloads
      - ./db.sqlite3:/app/db.sqlite3
      - ./logs:/app/logs
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
```

#### 3. **Deploy with Docker**
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Update
docker-compose pull && docker-compose up -d
```

### **Option 3: Cloud Deployment**

#### **Google Cloud Run**
```bash
# Build for Cloud Run
gcloud builds submit --config cloudbuild.yaml

# Deploy
gcloud run deploy whatsapp-ai-bot \
  --image gcr.io/YOUR-PROJECT/whatsapp-ai-bot \
  --platform managed \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY=your-key
```

#### **AWS ECS/Fargate**
```json
{
  "family": "whatsapp-ai-bot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "whatsapp-bot",
      "image": "your-account.dkr.ecr.region.amazonaws.com/whatsapp-ai-bot:latest",
      "environment": [
        {
          "name": "GEMINI_API_KEY",
          "value": "your-api-key"
        }
      ]
    }
  ]
}
```

## 🔧 Production Optimizations

### 1. **Performance Improvements**
```python
# Add to main script:

# Rate limiting
import asyncio
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests=10, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
    
    async def is_allowed(self, user_id):
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Clean old requests
        user_requests[:] = [req_time for req_time in user_requests 
                           if now - req_time < self.window]
        
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True
        return False

# Database for user management
import sqlite3

class UserManager:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_premium BOOLEAN DEFAULT FALSE
            )
        """)
        conn.commit()
        conn.close()
```

### 2. **Monitoring & Alerts**
```python
# Add logging and monitoring
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Metrics collection
class BotMetrics:
    def __init__(self):
        self.command_count = defaultdict(int)
        self.error_count = defaultdict(int)
        self.download_stats = defaultdict(int)
    
    def log_command(self, command, user_id):
        self.command_count[command] += 1
        logging.info(f"Command: {command}, User: {user_id}")
    
    def log_error(self, error_type, details):
        self.error_count[error_type] += 1
        logging.error(f"Error: {error_type}, Details: {details}")
```

### 3. **Security Enhancements**
```python
# Add security features
class SecurityManager:
    def __init__(self):
        self.blocked_users = set()
        self.admin_users = set()
    
    def is_blocked(self, user_id):
        return user_id in self.blocked_users
    
    def is_admin(self, user_id):
        return user_id in self.admin_users
    
    def validate_url(self, url):
        # Enhanced URL validation
        import re
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme in ['http', 'https']:
                return False
            
            # Block suspicious domains
            blocked_domains = ['malware.com', 'spam.site']
            if any(domain in parsed.netloc for domain in blocked_domains):
                return False
                
            return True
        except:
            return False
```

## 📊 Maintenance & Monitoring

### 1. **Health Checks**
```bash
# Create health check script
cat > health_check.sh << EOF
#!/bin/bash

# Check if bot process is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Bot is running"
else
    echo "❌ Bot is not running"
    sudo systemctl restart whatsapp-ai-bot
fi

# Check disk space
DISK_USAGE=$(df /home/ubuntu/whatsapp-ai-bot | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️ Disk usage high: ${DISK_USAGE}%"
    # Cleanup old files
    find /home/ubuntu/whatsapp-ai-bot/downloads -type f -mtime +1 -delete
fi

# Check yt-dlp updates
yt-dlp --version > /tmp/current_version
if ! cmp -s /tmp/current_version /tmp/last_version 2>/dev/null; then
    echo "📱 Updating yt-dlp..."
    sudo yt-dlp -U
    cp /tmp/current_version /tmp/last_version
fi
EOF

chmod +x health_check.sh

# Add to crontab
echo "*/5 * * * * /home/ubuntu/whatsapp-ai-bot/health_check.sh" | crontab -
```

### 2. **Backup Strategy**
```bash
# Create backup script
cat > backup.sh << EOF
#!/bin/bash

BACKUP_DIR="/backup/whatsapp-bot"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz *.log

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "✅ Backup completed: $DATE"
EOF

# Run daily backup
echo "0 2 * * * /home/ubuntu/whatsapp-ai-bot/backup.sh" | crontab -
```

## 💰 Cost Considerations

### **Gemini API Costs:**
- Input: $0.00125 per 1K tokens
- Output: $0.005 per 1K tokens
- Images: $0.00025 per image
- Audio: Variable based on duration

### **Server Costs (Monthly):**
- **VPS (2GB RAM)**: $10-20
- **Cloud Run**: $0 (with free tier) + usage
- **AWS ECS**: $15-30
- **Bandwidth**: Variable based on downloads

### **Cost Optimization:**
1. Implement user limits
2. Cache frequently requested content
3. Use compression for large files
4. Implement premium features for heavy users

## 🎯 Conclusion

Script ini adalah implementasi yang solid untuk WhatsApp AI Bot dengan fitur-fitur canggih. Deployment sebaiknya dilakukan di VPS dengan monitoring yang baik untuk memastikan stabilitas dan performa optimal.

**Key Success Factors:**
- ✅ Proper environment setup
- ✅ Regular maintenance & updates
- ✅ Monitoring & logging
- ✅ Cost management
- ✅ Security considerations
