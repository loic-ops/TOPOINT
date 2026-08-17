-- ============================================================
-- TOPOINT — Reset complet de la base + nouvel admin
-- Copier-coller dans Supabase > SQL Editor > Run
-- ============================================================

-- 1. Supprimer toutes les donnees
TRUNCATE pointages, pin_attempts CASCADE;
DELETE FROM employees;

-- 2. Ajouter la colonne is_archived si elle n'existe pas
ALTER TABLE pointages ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT FALSE;

-- 3. Creer le nouvel admin
INSERT INTO employees (matricule, first_name, last_name, role, pin_hash, salt, is_active, hourly_rate, created_at)
VALUES (
    'ADMIN-PROD',
    'Admin',
    'PROD',
    'admin',
    '0d0291be5f2d58e1ca728031b321a5ccf87ff0055e20dc2388ce9600a10d8d89',
    '9a83c8465202c7edd00227f3de62dc3b',
    TRUE,
    NULL,
    NOW()
);

-- Verification
SELECT id, matricule, first_name, last_name, role, is_active FROM employees;
