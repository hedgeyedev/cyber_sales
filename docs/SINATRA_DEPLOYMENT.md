# Sinatra Web App Deployment Guide

Simple web server for serving Cyber Sales reports without daily ZIP distribution.

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
cd /Users/fkchang/work/cyber_sales
bundle install
```

### 2. Set Credentials (Optional)

```bash
export REPORTS_USER=your_username
export REPORTS_PASS=your_secure_password
```

If not set, defaults to `hedgeye` / `change_me_in_production`

### 3. Start Server

```bash
bundle exec rackup -p 5678
```

### 4. Access Reports

Open browser to: **http://localhost:5678**

Login with credentials from step 2.

## Production Deployment Options

### Option 1: Local Server (Simplest)

**Best for:** Internal use on always-on Mac/Linux machine

```bash
# Start server (keeps running in background)
nohup bundle exec rackup -p 5678 > logs/sinatra.log 2>&1 &

# Access from network
http://YOUR_IP:5678
```

**Pros:**
- Zero infrastructure cost
- 2 minutes to deploy
- Works immediately

**Cons:**
- Machine must stay on
- Not accessible outside local network (without router config)

### Option 2: Docker Container (Recommended)

**Best for:** Portable deployment, cloud readiness

#### Build Image

```bash
docker build -t cyber-reports .
```

#### Run Container

```bash
docker run -d \
  --name cyber-reports \
  --restart unless-stopped \
  -p 5678:5678 \
  -e REPORTS_USER=your_username \
  -e REPORTS_PASS=your_secure_password \
  -v $(pwd)/cache:/app/cache \
  cyber-reports
```

#### Management Commands

```bash
# Check status
docker ps | grep cyber-reports

# View logs
docker logs cyber-reports

# Restart
docker restart cyber-reports

# Stop
docker stop cyber-reports

# Remove
docker rm -f cyber-reports
```

**Pros:**
- Isolated environment
- Easy restart/update
- Deploy anywhere (local or cloud)
- Auto-restart on crash

**Cons:**
- Requires Docker installed

### Option 3: Cloud Deployment

**DigitalOcean Droplet ($5/month):**

1. Create Ubuntu droplet
2. Install Docker: `curl -fsSL https://get.docker.com | sh`
3. Copy files: `scp -r . user@droplet-ip:~/cyber_sales`
4. SSH in and run Docker command from Option 2
5. Configure firewall to allow port 5678

**AWS EC2 / Azure VM:**
- Similar process to DigitalOcean
- Use t2.micro (free tier eligible)

**Pros:**
- Accessible from anywhere
- Professional setup
- Automatic backups available

**Cons:**
- Monthly cost ($5-10)
- Requires basic DevOps knowledge

## Auto-Refresh Data Setup

Reports are auto-updated when HTML files change on disk. Use cron to regenerate daily.

### Add Cron Job

```bash
crontab -e
```

Add this line:

```cron
# Refresh cyber sales reports daily at 6am
0 6 * * * cd /Users/fkchang/work/cyber_sales && ./refresh_analysis.sh >> logs/refresh.log 2>&1
```

**How it works:**
1. Cron runs `refresh_analysis.sh` at 6am daily
2. Script generates fresh HTML files
3. Sinatra serves new files immediately (no restart needed)
4. Users see latest data on next page refresh

### Manual Refresh

```bash
cd /Users/fkchang/work/cyber_sales
./refresh_analysis.sh
```

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | 5678 | Server port |
| `REPORTS_USER` | hedgeye | Basic auth username |
| `REPORTS_PASS` | change_me_in_production | Basic auth password |

### Change Port

```bash
# Local
PORT=8080 bundle exec rackup

# Docker
docker run -e PORT=8080 -p 8080:8080 cyber-reports
```

### Disable Authentication

Edit `app.rb` and comment out the `use Rack::Auth::Basic` block.

**NOT RECOMMENDED** unless behind firewall or VPN.

## Troubleshooting

### Port Already in Use

```bash
# Find what's using the port
lsof -i :5678

# Kill the process
kill -9 <PID>

# Or use different port
PORT=8080 bundle exec rackup
```

### Can't Access from Other Computers

**Check firewall:**
```bash
# macOS
sudo pfctl -d  # Disable firewall temporarily

# Linux
sudo ufw allow 5678
```

**Check server binding:**
- Verify `bind: '0.0.0.0'` in app.rb (not `127.0.0.1`)

### Reports Not Updating

**Check refresh script:**
```bash
./refresh_analysis.sh
# Look for errors
```

**Verify cron job:**
```bash
# Check if cron job exists
crontab -l

# Check logs
tail logs/refresh.log
```

### Authentication Not Working

**Verify credentials:**
```bash
# Print current env vars
echo $REPORTS_USER
echo $REPORTS_PASS

# Check Docker container env
docker exec cyber-reports env | grep REPORTS
```

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost:5678/health
# Should return: {"status":"ok","timestamp":"2025-11-12T..."}
```

Use for uptime monitoring services.

### Check Server Status

```bash
# Local
ps aux | grep rackup

# Docker
docker ps | grep cyber-reports
```

## Security Best Practices

### 1. Strong Passwords

```bash
# Generate random password
openssl rand -base64 32
```

### 2. HTTPS (Production)

Use reverse proxy (nginx, Caddy) for TLS termination:

```nginx
server {
  listen 443 ssl;
  server_name reports.yourcompany.com;

  ssl_certificate /path/to/cert.pem;
  ssl_certificate_key /path/to/key.pem;

  location / {
    proxy_pass http://localhost:5678;
    proxy_set_header Host $host;
  }
}
```

### 3. IP Whitelisting

Add to `app.rb` before routes:

```ruby
before do
  allowed_ips = ['10.0.0.0/8', '192.168.1.0/24']
  halt 403 unless allowed_ips.any? { |range|
    IPAddr.new(range).include?(request.ip)
  }
end
```

### 4. Firewall Rules

```bash
# Only allow from office IP
sudo ufw allow from YOUR_OFFICE_IP to any port 5678
```

## Upgrading

### Update Dependencies

```bash
bundle update
```

### Rebuild Docker Image

```bash
docker build -t cyber-reports .
docker stop cyber-reports
docker rm cyber-reports
# Run new container with same command as before
```

## Backup Strategy

### Automated Backups

Add to crontab:

```cron
# Backup cache directory daily at midnight
0 0 * * * tar -czf ~/backups/cyber_cache_$(date +\%Y\%m\%d).tar.gz /Users/fkchang/work/cyber_sales/cache/
```

### Manual Backup

```bash
# Backup everything
tar -czf cyber_sales_backup.tar.gz .

# Restore
tar -xzf cyber_sales_backup.tar.gz
```

## Performance

### Expected Performance

- **Request latency:** < 50ms (static files)
- **Memory usage:** ~50-100 MB
- **CPU usage:** Near zero (idle)
- **Concurrent users:** 100+ (more than enough for internal use)

### Scaling (If Needed)

Add load balancer + multiple containers:

```bash
# Run multiple instances
docker run -d --name cyber-reports-1 -p 5678:5678 cyber-reports
docker run -d --name cyber-reports-2 -p 5679:5678 cyber-reports
docker run -d --name cyber-reports-3 -p 5680:5678 cyber-reports

# Add nginx load balancer
# (configuration not shown)
```

**You probably won't need this** for internal company use.

## Decommissioning Daily ZIP Workflow

Once Sinatra app is running smoothly:

1. **Week 1:** Run both (ZIP + web app) in parallel
2. **Week 2:** Ask users for feedback
3. **Week 3:** Announce deprecation of ZIP distribution
4. **Week 4:** Stop creating daily ZIPs

**Keep `package_reports.sh`** for:
- Board meetings (offline distribution)
- Compliance archives
- Special requests

## Cost Analysis

| Deployment | Setup Time | Monthly Cost | Maintenance |
|-----------|------------|--------------|-------------|
| Local server | 5 min | $0 | 0 min/week |
| Docker (local) | 10 min | $0 | 0 min/week |
| Cloud VM | 1 hour | $5-10 | 5 min/month |

**ROI:** Time saved from daily ZIP creation: **~7 min/day = 40+ hours/year**

## Support

**Issues?**
1. Check this document
2. Check logs: `tail logs/sinatra.log` or `docker logs cyber-reports`
3. Verify environment variables are set correctly
4. Test locally before blaming Docker/cloud

**Questions?**
- Contact: Forrest Chang (original developer)
- Repository: /Users/fkchang/work/cyber_sales

---

**Last Updated:** November 2025
**Version:** 1.0
