# Agentic SRS Assistant

Hệ thống hỗ trợ tự động hóa việc tạo và quản lý Software Requirements Specification (SRS) sử dụng AI agents.

## Tính năng

- 🤖 Phân tích requirements tự động
- 📝 Tạo SRS documents theo templates chuẩn
- ✅ Validation và refinement tự động
- 🔄 Hỗ trợ nhiều định dạng output (Markdown, JSON, PDF)

## Cài đặt với Docker (Khuyến nghị)

Hệ thống được thiết kế để chạy hoàn toàn trong Docker, bao gồm application và database.

### Yêu cầu

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM trở lên

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd agentic-srs-assistant

# 2. Copy file environment
cp env.example .env

# 3. Cấu hình .env file (quan trọng: thêm OPENAI_API_KEY)
# Mở .env và thêm API key của bạn:
# OPENAI_API_KEY=your_actual_api_key_here

# 4. Build và chạy với Docker Compose
docker-compose up -d

# 5. Truy cập ứng dụng
# Streamlit UI: http://localhost:8501
# PostgreSQL: localhost:5432
```

### Testing Docker Setup

Sau khi start services, verify infrastructure hoạt động đúng:

```bash
# Chạy test script tự động
python scripts/test_docker_setup.py

# Hoặc test thủ công
docker-compose ps  # Kiểm tra containers đang chạy
docker-compose logs postgres  # Xem PostgreSQL logs
docker-compose logs app  # Xem app logs
```

Xem [docs/DOCKER_SETUP.md](./docs/DOCKER_SETUP.md) để biết chi tiết về testing và troubleshooting.

### Các lệnh Docker thường dùng

```bash
# Khởi động tất cả services
docker-compose up -d

# Xem logs
docker-compose logs -f app

# Dừng tất cả services
docker-compose down

# Dừng và xóa volumes (xóa database)
docker-compose down -v

# Rebuild application
docker-compose build app

# Restart một service cụ thể
docker-compose restart app

# Chạy với pgAdmin (database management tool)
docker-compose --profile tools up -d
# pgAdmin sẽ có tại: http://localhost:5050
```

### Development Mode

Để phát triển với hot-reload:

```bash
# Sử dụng docker-compose.dev.yml
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Cài đặt Local (Không dùng Docker)

Nếu bạn muốn chạy local mà không dùng Docker:

```bash
# Clone repository
git clone <repository-url>
cd agentic-srs-assistant

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate

# Cài đặt dependencies
pip install -e .

# Cần PostgreSQL đang chạy và cấu hình DATABASE_URL trong .env
```

## Cấu hình

Tạo file `.env` từ `env.example`:

```bash
cp env.example .env
```

Cấu hình các biến môi trường trong `.env`:

```env
# Database (cho Docker)
POSTGRES_DB=srs_assistant
POSTGRES_USER=srs_user
POSTGRES_PASSWORD=your_secure_password

# LLM Configuration (BẮT BUỘC)
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
LOG_LEVEL=INFO
OUTPUT_DIR=./output
```

Xem `env.example` để biết tất cả các options có sẵn.

## Cấu trúc Project

```
agentic-srs-assistant/
├── main.py              # Entry point
├── pyproject.toml       # Project configuration
├── .cursorrules         # Cursor IDE rules
├── ARCHITECTURE.md      # System architecture documentation
├── README.md            # This file
├── src/                 # Source code (to be created)
├── tests/               # Test files (to be created)
└── docs/                # Documentation (to be created)
```

## Project Phases

Xem [PROJECT_PHASES.md](./PROJECT_PHASES.md) để hiểu rõ breakdown của dự án thành các phases và timeline.

## Development

### Sử dụng Makefile (Khuyến nghị)

```bash
# Xem tất cả commands có sẵn
make help

# Development mode
make dev

# Production mode
make prod

# Xem logs
make logs-app

# Backup database
make backup-db

# Restore database
make restore-db FILE=backup.sql
```

### Manual Commands

Xem [ARCHITECTURE.md](./ARCHITECTURE.md) để hiểu rõ về kiến trúc hệ thống.

## Troubleshooting

### Database connection issues

```bash
# Kiểm tra PostgreSQL đang chạy
docker-compose ps postgres

# Xem logs database
docker-compose logs postgres

# Test connection
docker-compose exec app python -c "import psycopg2; psycopg2.connect('postgresql://srs_user:srs_password@postgres:5432/srs_assistant')"
```

### Application không start

```bash
# Rebuild image
docker-compose build app

# Xem logs chi tiết
docker-compose logs -f app

# Kiểm tra environment variables
docker-compose exec app env | grep OPENAI
```

### Reset toàn bộ (⚠️ Xóa tất cả data)

```bash
# Dừng và xóa volumes
docker-compose down -v

# Xóa images
docker-compose down --rmi all

# Start lại từ đầu
docker-compose up -d
```

## License

[To be determined]

