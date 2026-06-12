-- ============================================
-- Cowork-Local v3.4.1: Booking Agency Tables
-- ============================================

-- Pacientes
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT DEFAULT '',
    email TEXT,
    phone TEXT,
    telegram_chat_id TEXT UNIQUE,
    id_type TEXT,  -- 'cedula', 'ruc', 'pasaporte'
    doc_id TEXT UNIQUE,  -- numero de documento (llave universal)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Disponibilidad (horarios del consultorio)
CREATE TABLE IF NOT EXISTS availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    slot_duration_minutes SMALLINT DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE
);

-- Citas
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    start_time TIMESTAMPTZ NOT NULL,
    duration_minutes SMALLINT DEFAULT 30,
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending','confirmed','cancelled','completed','no_show')),
    ics_uid TEXT,
    source_channel TEXT DEFAULT 'telegram',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_appointments_start ON appointments(start_time);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);

-- Historial de estados
CREATE TABLE IF NOT EXISTS appointment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT DEFAULT 'system',
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- FAQs
CREATE TABLE IF NOT EXISTS faqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT DEFAULT 'general'
);

-- Cola de emails (respeta límite Mail.ru 1/min)
CREATE TABLE IF NOT EXISTS email_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    to_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT,
    ics_path TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','sent','failed')),
    error_msg TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status);

-- ============================================
-- Datos iniciales
-- ============================================

INSERT INTO availability (weekday, start_time, end_time) VALUES
(0, '08:00', '17:00'),
(1, '08:00', '17:00'),
(2, '08:00', '17:00'),
(3, '08:00', '17:00'),
(4, '08:00', '17:00')
ON CONFLICT DO NOTHING;

INSERT INTO faqs (question, answer, category) VALUES
('¿Qué servicios tienen?', 'Consulta médica general de 30 minutos.', 'servicios'),
('¿Cuánto cuesta?', 'La consulta cuesta $30.', 'precios'),
('¿Dónde están ubicados?', 'Estamos en el centro de la ciudad.', 'ubicación'),
('¿Hay parqueadero?', '¡Sí! Tenemos parqueadero gratuito.', 'ubicación'),
('¿Aceptan tarjetas?', 'Sí, aceptamos Visa y Mastercard.', 'pagos'),
('¿Cuánto dura la consulta?', '30 minutos.', 'servicios'),
('¿Atienden fines de semana?', 'Lunes a viernes de 8:00 a 17:00.', 'horarios'),
('¿Puedo cancelar mi cita?', '¡Claro! Solo avísame con tiempo.', 'cancelaciones')
ON CONFLICT DO NOTHING;

-- ============================================
-- Accounting: Facturas electrónicas (SRI)
-- ============================================
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numero_factura TEXT NOT NULL,
    ruc_emisor TEXT NOT NULL,
    razon_social TEXT,
    fecha_emision DATE,
    subtotal DECIMAL(12,2),
    iva DECIMAL(12,2),
    total DECIMAL(12,2),
    source_email TEXT,
    attachment_path TEXT,
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(numero_factura, ruc_emisor)
);
