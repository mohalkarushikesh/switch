# Database Setup Guide for Oryza

## Prerequisites

1. **Docker Desktop** installed and running
2. **Docker Compose** (comes with Docker Desktop)
3. At least 4GB of free RAM
4. 10GB of free disk space

## Quick Start

### 1. Start All Databases

```bash
# From the project root directory
docker-compose -f docker-compose.db.yml up -d
```

This will start:
- **PostgreSQL** (Main database) - Port 5432
- **Redis** (Cache & Real-time) - Port 6379
- **MongoDB** (Unstructured data) - Port 27017
- **TimescaleDB** (Time-series data) - Port 5433
- **Adminer** (Database UI) - Port 8090

### 2. Verify Databases are Running

```bash
docker-compose -f docker-compose.db.yml ps
```

All services should show as "Up".

### 3. Access Database UIs

- **Adminer**: http://localhost:8090
  - System: PostgreSQL
  - Server: postgres
  - Username: oryza_user
  - Password: oryza_secure_pass_2024
  - Database: oryza_db

## Database Details

### PostgreSQL (Main Database)
- **Host**: localhost
- **Port**: 5432
- **Database**: oryza_db
- **Username**: oryza_user
- **Password**: oryza_secure_pass_2024
- **Connection String**: `postgresql://oryza_user:oryza_secure_pass_2024@localhost:5432/oryza_db`

### Redis (Cache)
- **Host**: localhost
- **Port**: 6379
- **Password**: oryza_redis_pass_2024
- **Connection String**: `redis://:oryza_redis_pass_2024@localhost:6379`

### MongoDB (NoSQL)
- **Host**: localhost
- **Port**: 27017
- **Database**: oryza_nosql
- **Username**: oryza_mongo
- **Password**: oryza_mongo_pass_2024
- **Connection String**: `mongodb://oryza_mongo:oryza_mongo_pass_2024@localhost:27017/oryza_nosql?authSource=admin`

### TimescaleDB (Time-Series)
- **Host**: localhost
- **Port**: 5433
- **Database**: oryza_timeseries
- **Username**: oryza_ts_user
- **Password**: oryza_ts_pass_2024
- **Connection String**: `postgresql://oryza_ts_user:oryza_ts_pass_2024@localhost:5433/oryza_timeseries`

## Test Database Connections

### Test PostgreSQL
```bash
docker exec -it oryza-postgres psql -U oryza_user -d oryza_db -c "SELECT 'PostgreSQL is working!' as status;"
```

### Test Redis
```bash
docker exec -it oryza-redis redis-cli -a oryza_redis_pass_2024 ping
```

### Test MongoDB
```bash
docker exec -it oryza-mongodb mongosh --username oryza_mongo --password oryza_mongo_pass_2024 --authenticationDatabase admin --eval "db.adminCommand('ping')"
```

### Test TimescaleDB
```bash
docker exec -it oryza-timescale psql -U oryza_ts_user -d oryza_timeseries -c "SELECT 'TimescaleDB is working!' as status;"
```

## View Database Schema

The database is automatically initialized with:
- Complete schema with all tables
- Seed data including test users, stocks, portfolios
- Sample transactions and news articles

### View Tables in PostgreSQL
```bash
docker exec -it oryza-postgres psql -U oryza_user -d oryza_db -c "\dt"
```

### View Collections in MongoDB
```bash
docker exec -it oryza-mongodb mongosh --username oryza_mongo --password oryza_mongo_pass_2024 --authenticationDatabase admin oryza_nosql --eval "db.getCollectionNames()"
```

## Stop Databases

```bash
docker-compose -f docker-compose.db.yml down
```

To also remove data volumes (WARNING: This deletes all data):
```bash
docker-compose -f docker-compose.db.yml down -v
```

## Troubleshooting

### Port Already in Use
If you get a "port already allocated" error:
1. Check what's using the port: `netstat -ano | findstr :5432`
2. Either stop the conflicting service or change the port in docker-compose.db.yml

### Cannot Connect to Database
1. Ensure Docker is running
2. Check if containers are up: `docker-compose -f docker-compose.db.yml ps`
3. Check logs: `docker-compose -f docker-compose.db.yml logs postgres`

### Permission Denied
Run PowerShell as Administrator or use Docker Desktop UI to manage containers.

## Next Steps

1. Start the backend services
2. Run database migrations (if any)
3. Test API endpoints
4. Start the frontend application 