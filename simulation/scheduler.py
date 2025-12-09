# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

import time
import logging
from datetime import datetime
from typing import Callable, Optional

class SimulationScheduler:
    """
    Scheduler for coordinating simulation data sources.
    Handles synchronization, retries, and logging.
    """
    
    def __init__(self, interval: int = 60):
        """
        Initialize the scheduler with a default interval in seconds.
        
        Args:
            interval: Time in seconds between simulation ticks
        """
        self.interval = interval
        self.running = False
        self.tasks = []
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Configure and return a logger instance."""
        logger = logging.getLogger('SimulationScheduler')
        logger.setLevel(logging.INFO)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        
        # Add handler to logger
        if not logger.handlers:
            logger.addHandler(ch)
        
        return logger
    
    def add_task(self, task_func: Callable, name: str, interval: Optional[int] = None):
        """
        Add a task to the scheduler.
        
        Args:
            task_func: Function to execute
            name: Name of the task for logging
            interval: Optional custom interval for this task
        """
        self.tasks.append({
            'func': task_func,
            'name': name,
            'interval': interval or self.interval,
            'last_run': 0
        })
    
    def start(self):
        """Start the scheduler."""
        self.running = True
        self.logger.info("Starting simulation scheduler...")
        
        try:
            while self.running:
                current_time = time.time()
                
                for task in self.tasks:
                    if current_time - task['last_run'] >= task['interval']:
                        try:
                            self.logger.debug(f"Running task: {task['name']}")
                            task['func']()
                            task['last_run'] = current_time
                        except Exception as e:
                            self.logger.error(f"Error in task {task['name']}: {str(e)}", exc_info=True)
                
                time.sleep(1)  # Prevent busy waiting
                
        except KeyboardInterrupt:
            self.logger.info("Simulation scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {str(e)}", exc_info=True)
        finally:
            self.stop()
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        self.logger.info("Simulation scheduler stopped")
