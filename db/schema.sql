CREATE DATABASE IF NOT EXISTS deepinsight_agent
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE deepinsight_agent;

CREATE TABLE IF NOT EXISTS research_runs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  thread_id VARCHAR(64) NOT NULL,
  topic VARCHAR(512) NOT NULL,
  depth ENUM('quick', 'deep') NOT NULL DEFAULT 'quick',
  status ENUM('planned', 'running', 'awaiting_human', 'completed', 'failed') NOT NULL DEFAULT 'running',
  outline_json JSON NULL,
  human_feedback TEXT NULL,
  critique_notes_json JSON NULL,
  final_report MEDIUMTEXT NULL,
  output_path VARCHAR(1024) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_research_runs_thread_id (thread_id),
  KEY idx_research_runs_status (status),
  KEY idx_research_runs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS research_findings (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  run_id BIGINT UNSIGNED NOT NULL,
  section_title VARCHAR(512) NOT NULL,
  summary TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_research_findings_run_id (run_id),
  CONSTRAINT fk_research_findings_run
    FOREIGN KEY (run_id) REFERENCES research_runs(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS research_sources (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  finding_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(1024) NOT NULL,
  url TEXT NOT NULL,
  snippet TEXT NULL,
  score DECIMAL(8, 5) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_research_sources_finding_id (finding_id),
  CONSTRAINT fk_research_sources_finding
    FOREIGN KEY (finding_id) REFERENCES research_findings(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

