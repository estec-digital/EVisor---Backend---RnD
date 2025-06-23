#!/bin/sh

# Chờ MinIO sẵn sàng
sleep 5

# Tạo bucket tên là mybucket
mc alias set local http://localhost:9000 minioadmin Ev1s0r2025
mc mb -p local/estec || true