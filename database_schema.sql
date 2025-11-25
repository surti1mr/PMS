# =============================================================
# Stand-Up Comedy Event Participation Management System
# Database Schema Structure (MySQL)
# 
# This file contains only the database structure:
# - Drop tables (children first)
# - Create tables (PKs, FKs, constraints)
# - Indexes and additional constraints
# 
# Note: This file does NOT contain any INSERT statements.
# =============================================================

# ---------------------------
# 1) Drop tables (children first)
# ---------------------------
DROP TABLE IF EXISTS registration;
DROP TABLE IF EXISTS event;
DROP TABLE IF EXISTS event_manager;
DROP TABLE IF EXISTS participant;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS registration_status;
DROP TABLE IF EXISTS event_status;
DROP TABLE IF EXISTS event_type;

# ---------------------------
# 2) Create master tables
# ---------------------------

# Event types
CREATE TABLE IF NOT EXISTS event_type (
  event_type_id INT AUTO_INCREMENT PRIMARY KEY,
  type_name VARCHAR(100) NOT NULL,
  type_description VARCHAR(255),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# Event statuses
CREATE TABLE IF NOT EXISTS event_status (
  event_status_id INT AUTO_INCREMENT PRIMARY KEY,
  status_name VARCHAR(60) NOT NULL,
  status_description VARCHAR(255),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# Registration statuses
CREATE TABLE IF NOT EXISTS registration_status (
  registration_status_id INT AUTO_INCREMENT PRIMARY KEY,
  status_name VARCHAR(60) NOT NULL,
  status_description VARCHAR(255),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# Admins
CREATE TABLE IF NOT EXISTS admin (
  admin_id INT AUTO_INCREMENT PRIMARY KEY,
  role VARCHAR(60) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(80) NOT NULL,
  last_name VARCHAR(80) NOT NULL,
  phone_number VARCHAR(30),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# Event managers
CREATE TABLE IF NOT EXISTS event_manager (
  event_manager_id INT AUTO_INCREMENT PRIMARY KEY,
  created_by_admin_id INT NOT NULL,
  role VARCHAR(60) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(80) NOT NULL,
  last_name VARCHAR(80) NOT NULL,
  phone_number VARCHAR(30),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  CONSTRAINT fk_em_admin FOREIGN KEY (created_by_admin_id)
    REFERENCES admin(admin_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# Participants
CREATE TABLE IF NOT EXISTS participant (
  participant_id INT AUTO_INCREMENT PRIMARY KEY,
  role VARCHAR(60) DEFAULT 'attendee',
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(80) NOT NULL,
  last_name VARCHAR(80) NOT NULL,
  phone_number VARCHAR(30),
  city VARCHAR(80),
  state VARCHAR(60),
  country VARCHAR(60),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# ---------------------------
# 3) Create dependent tables
# ---------------------------

# Events
CREATE TABLE IF NOT EXISTS event (
  event_id INT AUTO_INCREMENT PRIMARY KEY,
  event_manager_id INT NOT NULL,
  event_type_id INT NOT NULL,
  event_status_id INT NOT NULL,
  event_name VARCHAR(150) NOT NULL,
  event_description TEXT,
  event_date DATETIME NOT NULL,
  location VARCHAR(255),
  total_spots INT UNSIGNED,
  registration_deadline DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_event_manager FOREIGN KEY (event_manager_id)
    REFERENCES event_manager(event_manager_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_event_type FOREIGN KEY (event_type_id)
    REFERENCES event_type(event_type_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_event_status FOREIGN KEY (event_status_id)
    REFERENCES event_status(event_status_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# Registrations
CREATE TABLE IF NOT EXISTS registration (
  registration_id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  participant_id INT NOT NULL,
  registration_status_id INT NOT NULL,
  additional_info VARCHAR(255),
  registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status_updated_at DATETIME DEFAULT NULL,
  updated_by_event_manager_id INT DEFAULT NULL,
  CONSTRAINT fk_reg_event FOREIGN KEY (event_id)
    REFERENCES event(event_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_reg_participant FOREIGN KEY (participant_id)
    REFERENCES participant(participant_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_reg_status FOREIGN KEY (registration_status_id)
    REFERENCES registration_status(registration_status_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_reg_updated_by FOREIGN KEY (updated_by_event_manager_id)
    REFERENCES event_manager(event_manager_id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# ---------------------------
# 4) Indexes and additional constraints
# ---------------------------
ALTER TABLE event ADD CONSTRAINT uq_event_name_date UNIQUE (event_name, event_date);

CREATE INDEX idx_event_manager ON event(event_manager_id);
CREATE INDEX idx_event_status ON event(event_status_id);
CREATE INDEX idx_event_type ON event(event_type_id);
CREATE INDEX idx_reg_event ON registration(event_id);
CREATE INDEX idx_reg_participant ON registration(participant_id);
CREATE INDEX idx_reg_status ON registration(registration_status_id);

# ---------------------------
# End of schema structure
# ---------------------------

