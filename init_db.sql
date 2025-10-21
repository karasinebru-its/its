-- İlaç Takip Sistemi Database Migration Script
-- PostgreSQL için ilk kurulum

-- Kullanıcılar tablosu
CREATE TABLE IF NOT EXISTS "user" (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İlaçlar tablosu
CREATE TABLE IF NOT EXISTS medication (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES "user"(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    dosage VARCHAR(50) NOT NULL,
    time TIME NOT NULL,
    period VARCHAR(20) DEFAULT 'daily',
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_taken TIMESTAMP
);

-- Alınan ilaçlar tablosu
CREATE TABLE IF NOT EXISTS taken_medication (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES "user"(id) ON DELETE CASCADE,
    medication_id VARCHAR(36) REFERENCES medication(id),
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date DATE DEFAULT CURRENT_DATE
);

-- Ölçümler tablosu
CREATE TABLE IF NOT EXISTS measurement (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES "user"(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    systolic INTEGER,
    diastolic INTEGER,
    value FLOAT NOT NULL,
    unit VARCHAR(10) NOT NULL,
    notes TEXT,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İndeksler (performans için)
CREATE INDEX IF NOT EXISTS idx_medication_user_id ON medication(user_id);
CREATE INDEX IF NOT EXISTS idx_medication_time ON medication(time);
CREATE INDEX IF NOT EXISTS idx_medication_active ON medication(is_active);
CREATE INDEX IF NOT EXISTS idx_taken_medication_user_date ON taken_medication(user_id, date);
CREATE INDEX IF NOT EXISTS idx_measurement_user_type ON measurement(user_id, type);
CREATE INDEX IF NOT EXISTS idx_measurement_date ON measurement(measured_at);

-- Test kullanıcısı (geliştirme için)
INSERT INTO "user" (id, email, created_at)
VALUES ('test-user-id', 'test@example.com', CURRENT_TIMESTAMP)
ON CONFLICT (email) DO NOTHING;

-- Örnek ilaç verileri (test için)
INSERT INTO medication (id, user_id, name, dosage, time, period, is_active, created_at)
VALUES
    ('med-aspirin', 'test-user-id', 'Aspirin', '1 tablet', '08:30:00', 'daily', true, CURRENT_TIMESTAMP),
    ('med-insulin', 'test-user-id', 'İnsülin', '10 ünite', '07:00:00', 'daily', true, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

COMMIT;

-- Tablo yapısını kontrol et
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE tablename IN ('user', 'medication', 'taken_medication', 'measurement')
ORDER BY tablename;
