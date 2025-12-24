"""
Job Manager - SQLite database layer for persistent job tracking
Allows dashboard to display job history even after browser is closed.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from utils.logger import logger


class JobManager:
    """Manages scrape jobs in SQLite database for persistent tracking"""
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    source_url TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    products_found INTEGER DEFAULT 0,
                    products_processed INTEGER DEFAULT 0,
                    reviews_posted INTEGER DEFAULT 0,
                    reviews_failed INTEGER DEFAULT 0,
                    images_generated INTEGER DEFAULT 0,
                    collections_processed INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Job logs table for detailed tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    log_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            ''')
            
            conn.commit()
            logger.info(f"📦 Job database initialized at {self.db_path}")
    
    def _generate_task_id(self) -> str:
        """Generate a unique task ID like 'task_8c1d6e93c7de71e1'"""
        return f"task_{uuid.uuid4().hex[:16]}"
    
    def create_job(self, source_url: str) -> Dict:
        """Create a new scrape job"""
        task_id = self._generate_task_id()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO jobs (task_id, source_url, status, created_at, updated_at)
                VALUES (?, ?, 'running', ?, ?)
            ''', (task_id, source_url, datetime.now(), datetime.now()))
            job_id = cursor.lastrowid
            conn.commit()
        
        logger.info(f"📝 Created job {task_id} for {source_url}")
        return self.get_job(task_id)
    
    def update_job(self, task_id: str, **kwargs) -> Optional[Dict]:
        """Update a job's fields"""
        allowed_fields = [
            'status', 'products_found', 'products_processed', 
            'reviews_posted', 'reviews_failed', 'images_generated',
            'collections_processed', 'error_message'
        ]
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return self.get_job(task_id)
        
        updates['updated_at'] = datetime.now()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [task_id]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE jobs SET {set_clause} WHERE task_id = ?
            ''', values)
            conn.commit()
        
        return self.get_job(task_id)
    
    def get_job(self, task_id: str) -> Optional[Dict]:
        """Get a specific job by task_id"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM jobs WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        return None
    
    def get_all_jobs(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all jobs ordered by creation date (newest first)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM jobs 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_dashboard_stats(self) -> Dict:
        """Get aggregate statistics for the dashboard"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get totals
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_jobs,
                    COALESCE(SUM(products_found), 0) as total_products,
                    COALESCE(SUM(reviews_posted), 0) as total_reviews_posted,
                    COALESCE(SUM(reviews_failed), 0) as total_reviews_failed,
                    COALESCE(SUM(images_generated), 0) as total_images,
                    COALESCE(SUM(collections_processed), 0) as total_collections
                FROM jobs
            ''')
            row = cursor.fetchone()
            
            # Get job status counts
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM jobs
                GROUP BY status
            ''')
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                'total_jobs': row[0],
                'total_products': row[1],
                'total_reviews_posted': row[2],
                'total_reviews_failed': row[3],
                'total_images': row[4],
                'total_collections': row[5],
                'jobs_running': status_counts.get('running', 0),
                'jobs_completed': status_counts.get('completed', 0),
                'jobs_failed': status_counts.get('failed', 0),
                'jobs_pending': status_counts.get('pending', 0)
            }
    
    def add_job_log(self, task_id: str, log_type: str, message: str):
        """Add a log entry for a job"""
        job = self.get_job(task_id)
        if not job:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO job_logs (job_id, log_type, message, created_at)
                VALUES (?, ?, ?, ?)
            ''', (job['id'], log_type, message, datetime.now()))
            conn.commit()
    
    def get_job_logs(self, task_id: str, limit: int = 100) -> List[Dict]:
        """Get logs for a specific job"""
        job = self.get_job(task_id)
        if not job:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM job_logs 
                WHERE job_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (job['id'], limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def delete_job(self, task_id: str) -> bool:
        """Delete a job and its logs"""
        job = self.get_job(task_id)
        if not job:
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM job_logs WHERE job_id = ?', (job['id'],))
            cursor.execute('DELETE FROM jobs WHERE task_id = ?', (task_id,))
            conn.commit()
        
        logger.info(f"🗑️ Deleted job {task_id}")
        return True


# Global instance for easy access
job_manager = JobManager()
