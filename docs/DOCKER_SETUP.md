# Docker Setup Guide

Hướng dẫn test và verify Docker infrastructure cho Agentic SRS Assistant.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM trở lên

## Quick Start

### 1. Setup Environment

Copy file environment từ template:

```bash
cp env.example .env
```

Cập nhật `.env` với các giá trị phù hợp, đặc biệt là `OPENAI_API_KEY` (bắt buộc).

### 2. Build Docker Images

```bash
docker-compose build
```

Hoặc sử dụng Makefile:

```bash
make build
```

### 3. Start Services

```bash
docker-compose up -d
```

Hoặc:

```bash
make up
```

### 4. Verify Services

Kiểm tra status của containers:

```bash
docker-compose ps
```

Hoặc:

```bash
make status
```

Bạn sẽ thấy output tương tự:

```
NAME           IMAGE                    STATUS
srs-postgres   postgres:16-alpine       Up (healthy)
srs-app        agentic-srs-assistant   Up
```

## Testing Docker Setup

### Automated Test Script

Chạy test script tự động để verify toàn bộ infrastructure:

```bash
python scripts/test_docker_setup.py
```

Script sẽ test:
- Docker Compose installation
- Containers running status
- PostgreSQL health check
- PostgreSQL connection từ app container
- PostgreSQL connection từ host (nếu port được map)
- Basic database operations

### Manual Testing

#### Test PostgreSQL Connection từ Host

```bash
docker-compose exec app python -c "import psycopg2; conn = psycopg2.connect('postgresql://srs_user:srs_password@postgres:5432/srs_assistant'); print('Connection successful'); conn.close()"
```

#### Test PostgreSQL Health Check

```bash
docker-compose exec postgres pg_isready -U srs_user -d srs_assistant
```

Expected output: `postgres:5432 - accepting connections`

#### Test Database Operations

```bash
docker-compose exec app python -c "
import psycopg2
conn = psycopg2.connect('postgresql://srs_user:srs_password@postgres:5432/srs_assistant')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS test (id SERIAL PRIMARY KEY, name TEXT)')
cur.execute('INSERT INTO test (name) VALUES (%s)', ('test',))
cur.execute('SELECT * FROM test')
print('Rows:', cur.fetchall())
cur.execute('DROP TABLE test')
conn.commit()
print('Database operations successful')
"
```

## Viewing Logs

### All Services

```bash
docker-compose logs -f
```

### App Service Only

```bash
docker-compose logs -f app
```

Hoặc:

```bash
make logs-app
```

### PostgreSQL Service Only

```bash
docker-compose logs -f postgres
```

Hoặc:

```bash
make logs-db
```

## Troubleshooting

### Containers Not Starting

1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Check for port conflicts:**
   ```bash
   # Check if port 8501 is in use
   netstat -an | grep 8501
   # Or on Linux
   lsof -i :8501
   ```

3. **View detailed logs:**
   ```bash
   docker-compose logs app
   docker-compose logs postgres
   ```

### PostgreSQL Connection Issues

1. **Verify PostgreSQL container is healthy:**
   ```bash
   docker-compose ps postgres
   ```
   Should show `(healthy)` status.

2. **Check PostgreSQL logs:**
   ```bash
   docker-compose logs postgres
   ```

3. **Test connection from container:**
   ```bash
   docker-compose exec postgres psql -U srs_user -d srs_assistant -c "SELECT version();"
   ```

4. **Verify environment variables:**
   ```bash
   docker-compose exec app env | grep POSTGRES
   ```

### App Container Issues

1. **Check if app container is running:**
   ```bash
   docker-compose ps app
   ```

2. **View app logs:**
   ```bash
   docker-compose logs -f app
   ```

3. **Check if dependencies are installed:**
   ```bash
   docker-compose exec app pip list
   ```

4. **Access container shell:**
   ```bash
   docker-compose exec app /bin/bash
   ```

### Build Issues

1. **Clean build (no cache):**
   ```bash
   docker-compose build --no-cache
   ```

2. **Rebuild specific service:**
   ```bash
   docker-compose build app
   ```

3. **Check Dockerfile syntax:**
   ```bash
   docker build -t test-image -f Dockerfile .
   ```

## Development Mode

Để chạy với hot-reload (code changes tự động reload):

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Hoặc:

```bash
make dev
```

## Production Mode

```bash
docker-compose up -d
```

Hoặc:

```bash
make prod
```

## Stopping Services

### Stop All Services

```bash
docker-compose down
```

Hoặc:

```bash
make down
```

### Stop and Remove Volumes (⚠️ Deletes Data)

```bash
docker-compose down -v
```

Hoặc:

```bash
make clean
```

## Database Management

### Access PostgreSQL Shell

```bash
docker-compose exec postgres psql -U srs_user -d srs_assistant
```

Hoặc:

```bash
make db-shell
```

### Backup Database

```bash
docker-compose exec postgres pg_dump -U srs_user srs_assistant > backup.sql
```

Hoặc:

```bash
make backup-db
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U srs_user srs_assistant < backup.sql
```

Hoặc:

```bash
make restore-db FILE=backup.sql
```

## pgAdmin (Optional)

Để chạy với pgAdmin (database management UI):

```bash
docker-compose --profile tools up -d
```

Hoặc:

```bash
make tools
```

Truy cập pgAdmin tại: http://localhost:5050

- Email: `admin@srs.local` (hoặc giá trị từ `PGADMIN_EMAIL` trong `.env`)
- Password: `admin` (hoặc giá trị từ `PGADMIN_PASSWORD` trong `.env`)

## Verification Checklist

Sau khi setup, verify các điểm sau:

- [ ] Docker containers đang chạy (`docker-compose ps`)
- [ ] PostgreSQL container healthy (`docker-compose ps postgres`)
- [ ] App container running (`docker-compose ps app`)
- [ ] PostgreSQL connection successful (chạy test script)
- [ ] Database operations working (chạy test script)
- [ ] App accessible tại http://localhost:8501 (sau khi implement UI)
- [ ] Logs không có errors (`docker-compose logs`)

## Next Steps

Sau khi Docker infrastructure đã được verify:

1. Proceed to Phase 0.3: Database Setup
2. Create database schema
3. Test database migrations
4. Continue với Phase 1: Core Models & Validation

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture details

