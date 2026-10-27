-- FairShare relational database schema
-- MySQL 8.0+
-- Safe to run repeatedly: CREATE TABLE IF NOT EXISTS preserves existing data.

CREATE DATABASE IF NOT EXISTS fairshare_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE fairshare_db;

CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `groups` (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  description VARCHAR(500) NULL,
  invite_code VARCHAR(16) NOT NULL,
  created_by INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_groups_invite_code (invite_code),
  KEY ix_groups_created_by (created_by),
  CONSTRAINT fk_groups_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS group_members (
  id INT NOT NULL AUTO_INCREMENT,
  group_id INT NOT NULL,
  user_id INT NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'member',
  joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_group_user (group_id, user_id),
  KEY ix_group_members_user (user_id),
  CONSTRAINT fk_group_members_group FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
  CONSTRAINT fk_group_members_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS expenses (
  id INT NOT NULL AUTO_INCREMENT,
  group_id INT NOT NULL,
  paid_by INT NOT NULL,
  title VARCHAR(160) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  category VARCHAR(50) NOT NULL DEFAULT 'Other',
  expense_date DATE NOT NULL,
  notes VARCHAR(500) NULL,
  PRIMARY KEY (id),
  KEY ix_expenses_group_date (group_id, expense_date),
  KEY ix_expenses_paid_by (paid_by),
  CONSTRAINT fk_expenses_group FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
  CONSTRAINT fk_expenses_payer FOREIGN KEY (paid_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS expense_splits (
  id INT NOT NULL AUTO_INCREMENT,
  expense_id INT NOT NULL,
  user_id INT NOT NULL,
  share_amount DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_expense_user (expense_id, user_id),
  KEY ix_expense_splits_user (user_id),
  CONSTRAINT fk_expense_splits_expense FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
  CONSTRAINT fk_expense_splits_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS settlements (
  id INT NOT NULL AUTO_INCREMENT,
  group_id INT NOT NULL,
  paid_by INT NOT NULL,
  paid_to INT NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  settlement_date DATE NOT NULL,
  note VARCHAR(300) NULL,
  PRIMARY KEY (id),
  KEY ix_settlements_group_date (group_id, settlement_date),
  KEY ix_settlements_paid_by (paid_by),
  KEY ix_settlements_paid_to (paid_to),
  CONSTRAINT fk_settlements_group FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
  CONSTRAINT fk_settlements_payer FOREIGN KEY (paid_by) REFERENCES users(id),
  CONSTRAINT fk_settlements_receiver FOREIGN KEY (paid_to) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS group_budgets (
  id INT NOT NULL AUTO_INCREMENT,
  group_id INT NOT NULL,
  monthly_limit DECIMAL(12,2) NOT NULL,
  updated_by INT NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_group_budgets_group (group_id),
  KEY ix_group_budgets_updated_by (updated_by),
  CONSTRAINT fk_group_budgets_group FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
  CONSTRAINT fk_group_budgets_user FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS activity_logs (
  id INT NOT NULL AUTO_INCREMENT,
  group_id INT NOT NULL,
  user_id INT NULL,
  action VARCHAR(80) NOT NULL,
  details VARCHAR(500) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_activity_logs_group (group_id),
  KEY ix_activity_logs_created_at (created_at),
  CONSTRAINT fk_activity_logs_group FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
  CONSTRAINT fk_activity_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- The tables are now explicitly defined in SQL. The Flask application also
-- calls SQLAlchemy db.create_all() at startup; it will leave existing tables/data intact.
