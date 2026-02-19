# Gunicorn configuration file for Fleet-Management

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 4  # Adjust based on CPU cores (2-4 x cores for web apps)
worker_class = "sync"
worker_connections = 1000
threads = 2  # Use threads for better concurrency
timeout = 30
keepalive = 2

# Worker process management
max_requests = 1000
max_requests_jitter = 50

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = "-"  # stdout
errorlog = "-"  # stdout
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "fleet-management"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure for HTTPS)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
