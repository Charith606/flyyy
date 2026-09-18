-- =============================================================================
-- Flyyy Privacy-Preserving Customer Data Platform (CDP) - MySQL 8.0 Schema
-- Architecture: Mandatory Access Model (Privacy Gateway Boundary)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `flyyy_cdp` 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE `flyyy_cdp`;

-- -----------------------------------------------------------------------------
-- 1. SOURCE DATA STORE (Read-Only Ingestion Boundary)
-- Contains raw ingestion data before privacy transformation.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `source_customers` (
    `customer_id` VARCHAR(50) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `mobile` VARCHAR(50) NOT NULL,
    `city` VARCHAR(100) NULL,
    `segment` VARCHAR(50) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`customer_id`),
    INDEX `idx_source_email` (`email`),
    INDEX `idx_source_mobile` (`mobile`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- 2. PROTECTED DATA STORE (Requestor Domain: Marketing / CRM / Analytics)
-- Accessible to downstream applications. Contains ZERO plaintext PII.
-- Uses FPE for phone numbers and HMAC tokens for emails/names.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `protected_customers` (
    `customer_id` VARCHAR(50) NOT NULL,
    `name_token` VARCHAR(100) NOT NULL,
    `email_token` VARCHAR(100) NOT NULL,
    `mobile_fpe` VARCHAR(50) NOT NULL,
    `city` VARCHAR(100) NULL,
    `segment` VARCHAR(50) NULL,
    `batch_id` VARCHAR(100) NULL,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`customer_id`),
    INDEX `idx_prot_name_token` (`name_token`),
    INDEX `idx_prot_email_token` (`email_token`),
    INDEX `idx_prot_mobile_fpe` (`mobile_fpe`),
    INDEX `idx_prot_batch_id` (`batch_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- 3. SECURE ISOLATED VAULT (Internal Gateway Only - Direct Access Blocked)
-- Stores AES-256-GCM encrypted mappings between tokens/ciphers & real PII.
-- Downstream applications are strictly forbidden from accessing this table.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `vault_mappings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `token_or_cipher` VARCHAR(150) NOT NULL UNIQUE,
    `field_type` VARCHAR(50) NOT NULL COMMENT 'EMAIL, NAME, MOBILE',
    `encrypted_plaintext` TEXT NOT NULL COMMENT 'Base64 encoded Nonce + Ciphertext + Tag (AES-256-GCM)',
    `key_reference` VARCHAR(50) NOT NULL DEFAULT 'default_v1',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_vault_token` (`token_or_cipher`),
    INDEX `idx_vault_field_type` (`field_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- 4. IMMUTABLE AUDIT LOG (Mandatory Monitoring & Compliance)
-- Records every request, authorized execution, and denied access attempt.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `audit_log` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `actor` VARCHAR(100) NOT NULL COMMENT 'User or Application identifier',
    `action` VARCHAR(100) NOT NULL COMMENT 'REVEAL_ATTEMPT, BLIND_CAMPAIGN_DISPATCH, BATCH_RUN, etc.',
    `subject_id` VARCHAR(100) NULL COMMENT 'Token or customer_id involved',
    `field` VARCHAR(50) NULL COMMENT 'EMAIL, MOBILE, FULL_RECORD',
    `purpose` VARCHAR(100) NULL COMMENT 'Business justification (e.g. TICKET-9921)',
    `reference_id` VARCHAR(100) NULL COMMENT 'Ticket or Campaign reference ID',
    `outcome` VARCHAR(50) NOT NULL COMMENT 'ALLOWED, ACCESS_DENIED',
    `ip_address` VARCHAR(50) NOT NULL DEFAULT '127.0.0.1',
    `details` TEXT NULL COMMENT 'JSON or descriptive metadata (NEVER logs plaintext PII)',
    `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_audit_actor` (`actor`),
    INDEX `idx_audit_action` (`action`),
    INDEX `idx_audit_subject` (`subject_id`),
    INDEX `idx_audit_outcome` (`outcome`),
    INDEX `idx_audit_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- 5. BATCH RUNS & PIPELINE METADATA
-- Tracks data ingestion batches and transformation lifecycle.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `batch_runs` (
    `batch_id` VARCHAR(100) NOT NULL,
    `source` VARCHAR(100) NOT NULL,
    `status` VARCHAR(50) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING, RUNNING, COMPLETED, FAILED',
    `row_count` INT NOT NULL DEFAULT 0,
    `success_count` INT NOT NULL DEFAULT 0,
    `error_count` INT NOT NULL DEFAULT 0,
    `start_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `end_time` DATETIME NULL,
    `error_details` TEXT NULL,
    PRIMARY KEY (`batch_id`),
    INDEX `idx_batch_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- 6. PROTECTION POLICIES
-- Configurable rules per column for automated classification and encryption.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `protection_policies` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `field_name` VARCHAR(100) NOT NULL UNIQUE,
    `entity_type` VARCHAR(100) NOT NULL COMMENT 'EMAIL_ADDRESS, PHONE_NUMBER, PERSON_NAME',
    `protection_type` VARCHAR(50) NOT NULL COMMENT 'FPE, TOKENIZATION, DYNAMIC_MASKING',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- INITIAL SEED: DEFAULT PROTECTION POLICIES
-- -----------------------------------------------------------------------------
INSERT INTO `protection_policies` (`field_name`, `entity_type`, `protection_type`, `is_active`)
VALUES 
    ('email', 'EMAIL_ADDRESS', 'TOKENIZATION', TRUE),
    ('mobile', 'PHONE_NUMBER', 'FPE', TRUE),
    ('name', 'PERSON_NAME', 'TOKENIZATION', TRUE)
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;
