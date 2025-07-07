CREATE TABLE IF NOT EXISTS "User" (
    "user_id" VARCHAR(255) UNIQUE,
    "full_name" VARCHAR(255),
    "username" VARCHAR(255),
    "phone_number" VARCHAR(255),
    "ext" INTEGER,
    "email" VARCHAR(255),
    "avatar" VARCHAR(255),
    "password" VARCHAR(255),
    "role_id" INTEGER,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "department_id" INTEGER,
    "factory_id" INTEGER,
    "language_id" VARCHAR(10),
    "is_active" BOOLEAN DEFAULT TRUE,
    "last_active_at" TIMESTAMP
);
COPY "User" ("user_id", "full_name", "username", "phone_number", "ext", "email", "avatar", "password", "role_id", "created_at", "updated_at", "department_id", "factory_id", "language_id", "is_active", "last_active_at")
FROM '/postgresql/data/ESTEC-User.csv'
DELIMITER ','
CSV HEADER;

CREATE TABLE IF NOT EXISTS "Session" (
    "session_id" UUID PRIMARY KEY,
    "user_id" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP DEFAULT NOW(),
    "expires_at" TIMESTAMP
);