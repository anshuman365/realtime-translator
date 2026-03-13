# Deployment Guide for Render

This guide will walk you through deploying the Real-Time Translator application on Render.

## Prerequisites

- GitHub account
- Render account (free tier available at https://render.com)
- Your code pushed to a GitHub repository

## Step-by-Step Deployment on Render

### Option 1: Using render.yaml (Recommended)

1. **Push Code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Connect to Render**
   - Go to https://dashboard.render.com
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Configure Environment Variables**
   
   Render will auto-generate some variables, but you should set:
   
   - `ADMIN_USERNAME`: Your admin username (default: admin)
   - `ADMIN_PASSWORD`: Strong password for admin access
   - `SECRET_KEY`: Generate with `openssl rand -hex 32`
   - `DATABASE_URL`: Leave as default for SQLite, or add PostgreSQL

4. **Deploy**
   - Click "Apply"
   - Render will build and deploy your application
   - First deployment takes 10-15 minutes (downloading models)

5. **Access Your Application**
   - Main app: `https://your-app-name.onrender.com`
   - Admin panel: `https://your-app-name.onrender.com/admin`

### Option 2: Manual Deployment

1. **Create Web Service**
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
   - **Name**: realtime-translator
   - **Region**: Choose closest to your users
   - **Branch**: main
   - **Runtime**: Docker
   - **Dockerfile Path**: ./Dockerfile
   - **Instance Type**: Standard (or higher for better performance)

3. **Environment Variables**
   Add these in the "Environment" section:
   
   ```
   DATABASE_URL=sqlite+aiosqlite:///./translation_app.db
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=<your-secure-password>
   SECRET_KEY=<generate-with-openssl-rand-hex-32>
   CORS_ORIGINS=*
   PORT=8000
   ```

4. **Advanced Settings**
   - **Health Check Path**: `/api/health`
   - **Auto-Deploy**: Yes

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (10-15 minutes first time)

## Post-Deployment Configuration

### 1. Update Frontend URLs

If you're serving the frontend separately, update:

```bash
REACT_APP_API_URL=https://your-app.onrender.com
REACT_APP_WS_URL=wss://your-app.onrender.com
```

### 2. Test the Deployment

- Visit `https://your-app.onrender.com/api/health`
- Should return: `{"status": "healthy", "version": "1.0.0"}`

### 3. Login to Admin Panel

- Go to `https://your-app.onrender.com/admin/login`
- Use your `ADMIN_USERNAME` and `ADMIN_PASSWORD`

## Upgrading to PostgreSQL (Optional)

For production with multiple users, upgrade to PostgreSQL:

1. **Create PostgreSQL Database**
   - In Render Dashboard, click "New" → "PostgreSQL"
   - Name: translator-db
   - Choose plan (Starter recommended)

2. **Update Environment Variable**
   - Copy the "Internal Database URL"
   - Update `DATABASE_URL` in your web service:
   ```
   DATABASE_URL=postgresql://<from-render>
   ```

3. **Redeploy**
   - Service will automatically restart
   - Database tables will be created on startup

## Performance Optimization

### For Better Performance on Render

1. **Upgrade Instance Type**
   - Go to Settings → Instance Type
   - Choose "Standard Plus" or higher
   - More CPU = faster translations

2. **Use Persistent Disk** (for model caching)
   - Settings → Disks → Add Disk
   - Mount Path: `/app/models`
   - Size: 2GB minimum
   - Models won't re-download on each deploy

3. **Enable HTTP/2**
   - Already enabled by default on Render
   - Improves WebSocket performance

## Monitoring

### View Logs
- Dashboard → Your Service → Logs
- Real-time logs of all requests and errors

### Metrics
- Dashboard → Your Service → Metrics
- CPU, Memory, Response times

### Health Checks
- Render automatically monitors `/api/health`
- Auto-restarts if unhealthy

## Troubleshooting

### Models Not Loading
**Problem**: "Model not found" errors

**Solution**:
1. Check logs during deployment
2. Ensure `download_models.sh` ran successfully
3. May need to increase deployment timeout

### WebSocket Disconnects
**Problem**: Frequent disconnections

**Solution**:
1. Upgrade instance type (more resources)
2. Check network/firewall settings
3. Enable persistent connections in Render settings

### High Latency
**Problem**: Translations taking >2 seconds

**Solutions**:
1. Upgrade to better instance type
2. Add persistent disk for model caching
3. Consider using smaller models (edit `config.py`)
4. Enable GPU instances (paid plan)

### Database Locked Errors
**Problem**: SQLite database locked

**Solution**:
- Upgrade to PostgreSQL (recommended for production)
- SQLite is single-writer, not ideal for multiple concurrent users

## Costs Estimate

### Free Tier
- 750 hours/month web service
- Sleeps after 15 min inactivity
- Limited to 512MB RAM
- **Good for**: Testing, demos, low usage

### Paid Plans
- **Starter ($7/month)**
  - No sleep
  - 512MB RAM
  - Good for 1-5 concurrent users

- **Standard ($25/month)**
  - 2GB RAM
  - Better performance
  - Good for 10-20 concurrent users

- **Standard Plus ($85/month)**
  - 4GB RAM
  - Production-ready
  - 50+ concurrent users

### PostgreSQL
- **Starter ($7/month)**: 1GB storage
- **Standard ($20/month)**: 10GB storage

## Security Recommendations

1. **Change Default Credentials**
   ```
   ADMIN_PASSWORD=<use-strong-password>
   SECRET_KEY=<use-openssl-rand-hex-32>
   ```

2. **Enable HTTPS** (automatic on Render)

3. **Restrict CORS** (for production)
   ```
   CORS_ORIGINS=https://yourdomain.com
   ```

4. **Rate Limiting**
   - Already implemented in code
   - Prevents abuse

5. **Regular Updates**
   - Enable auto-deploy from GitHub
   - Keep dependencies updated

## Custom Domain

1. **Add Domain in Render**
   - Settings → Custom Domain
   - Add your domain

2. **Update DNS**
   - Add CNAME record pointing to Render
   - Example: `CNAME realtime-translator.onrender.com`

3. **SSL Certificate**
   - Automatically provisioned by Render
   - Free Let's Encrypt certificate

## Backup and Recovery

### Backup Database
```bash
# For PostgreSQL
pg_dump <database-url> > backup.sql

# For SQLite (download from service)
# Not recommended for production
```

### Restore
```bash
# PostgreSQL
psql <database-url> < backup.sql
```

## Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **GitHub Issues**: Create issue in your repository

## Next Steps

After successful deployment:

1. Test all features (translation, admin panel)
2. Monitor performance and logs
3. Set up alerts in Render
4. Configure custom domain
5. Invite users and gather feedback

---

**Deployment Complete!** 🎉

Your real-time translator is now live and ready to use.
