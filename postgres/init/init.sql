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

CREATE TABLE IF NOT EXISTS "WorkManagement" (
    "task_id" SERIAL PRIMARY KEY,
    "owner" VARCHAR(255) NOT NULL,
    "full_name" VARCHAR(255) NOT NULL,
    "project_code" VARCHAR(255) NOT NULL,
    "description" VARCHAR(255) NOT NULL,
    "start_date" TIMESTAMP,
    "end_date" TIMESTAMP,
    "QTY" DECIMAL(10, 2),
    "site" VARCHAR(255) NOT NULL,
    "status" INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "WS_Statistical" (
    "id" SERIAL PRIMARY KEY,  
    "product_name" TEXT,
    "description" TEXT,
    "time" TIMESTAMP,
    "part_no" VARCHAR(255),
    "origin" VARCHAR(255),
    "entered_by" VARCHAR(255),
    "product_type" VARCHAR(255),
    "quantity" INTEGER,
    "unit" VARCHAR(50),
    "quantity" INTEGER,
    "seri_number" VARCHAR(255),
    "location" VARCHAR(255),
    "status" INTEGER DEFAULT 0,
    "manufacturing_date" TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "WS_Import" (
    "id" SERIAL PRIMARY KEY,    
    "import_id" VARCHAR(255),
    "time" TIMESTAMP,
    "import_time" TIMESTAMP, 
    "project_code" VARCHAR(255),            
    "product_name" VARCHAR(255),                      
    "part_no" VARCHAR(255),               
    "origin" VARCHAR(255),                  
    "quantity" INTEGER,                     
    "seri_number" VARCHAR(255),
    "deleted" BOOLEAN DEFAULT FALSE,
    "statistical_id" INTEGER REFERENCES "WS_Statistical"("id") ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "WS_Export" (
    "id" SERIAL PRIMARY KEY,
    "export_id" VARCHAR(255),
    "time" TIMESTAMP,      
    "export_time" TIMESTAMP,
    "project_code" VARCHAR(255),            
    "product_name" VARCHAR(255),                      
    "part_no" VARCHAR(255),               
    "origin" VARCHAR(255),                  
    "quantity" INTEGER,                     
    "seri_number" VARCHAR(255),
    "cabinet" VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS "WS_Installation" (
    "id" SERIAL PRIMARY KEY,
    "higher_lever_function" VARCHAR(255),
    "location" VARCHAR(255),      
    "dt" VARCHAR(255),
    "quantity" VARCHAR(255),            
    "description" VARCHAR(255),                      
    "part_no" VARCHAR(255),               
    "seri_number" VARCHAR(255) NULL,
    "manufacturer" VARCHAR(255),
    "project_code" VARCHAR(255),
    "cabinet_no" VARCHAR(255) NULL,
);
