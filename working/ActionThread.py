# ===============================================
# THREAD 2: ACTION / SCHEDULER
# ===============================================
import threading
from McLumk_Wheel_Sports import *
import time
#from Task import task, redTask, blueTask, greenTask
import Task
import config
from robot import Raspbot
# our files
import RotatoSettings
from Utils import current_milli_time
import RobotState
# allows for controlling input according to keyboard
debug = True
import queue # Thread safe implementation of queue
import RGBTasks

# Global variables for task management
color_to_task_idx = {
    0: 0,  # invalid
    1: 0,  # Red
    2: 1,  # Green
    3: 2,  # Blue
}
color_idx_to_color = {
    1: "Red",
    2: "Green",
    3: "Blue",
}

def action_thread_loop(shutdown_event):
    """
    This function runs in its own thread.
    Its job is to pull tasks from the queue and execute them.
    """
    
    print("[Thread 2] Action thread started. Waiting for tasks...")
    
    while not shutdown_event.is_set():
        try:
            # --- 1. Get Task from Queue ---
            # We use a timeout so this loop doesn't block forever
            # and can check the shutdown_event.
            try:
                task_data = RobotState.task_queue.get(timeout=1.0)
            except queue.Empty:
                # This is normal. No tasks. Just loop again.
                continue 

            color = task_data['color']
            centroid = task_data['centroid']
            task_idx = color_to_task_idx.get(color)
            
            if task_idx is None:
                print(f"[Thread 2] Error: Got unknown color index {color}")
                RobotState.task_queue.task_done()
                continue
            
            # Validate task index
            if task_idx < 0 or task_idx >= len(RGBTasks.tasks):
                print(f"[Thread 2] Error: Invalid task index {task_idx}")
                RobotState.task_queue.task_done()
                continue
            
            print(f"[Thread 2] Popped task {color_idx_to_color[color]} (Idx {task_idx}). Centroid: {task_data['centroid']}")
            
            current_task = RGBTasks.tasks[task_idx]

            # --- 3. Run Task ---
            # Execute task until completion or shutdown signal
            task_completed = False
            start_time = time.time()
            
            while not task_completed and not shutdown_event.is_set():
                # Safety check: abort if task takes too long
                if time.time() - start_time > RotatoSettings.roundRobinQuant:
                    print(f"[Thread 2] Task {task_idx} exceeded max duration. Leaving.")
                    break
                
                # Run task update and check if completed
                try:
                    task_completed = current_task.setup(centroid)
                except Exception as e:
                    print(f"[Thread 2] Error during task update: {e}")
                    break
                
                time.sleep(0.05)  # Control loop frequency (~20 Hz)

            if task_completed:
                print(f"--- Task {task_idx} finished (completed={task_completed}) ---")
                current_task.reset()  # Mark task as complete
                RobotState.tasks_in_queue.discard(color)
            else:
                print(f"--- Task {color} paused, appended back to queue ---")
                resume_task_data = {
                    'color': color,
                    'centroid': centroid,
                    'delta': task_data['delta']
                }

            # --- 4. Mark Task as Complete ---
            RobotState.task_queue.task_done()
            
        except Exception as e:
            print(f"[Thread 2] An error occurred: {e}")
            # In case of error, try to clean up
            if 'color' in locals():
                RobotState.tasks_in_queue.discard(color)
            if 'task_data' in locals():
                RobotState.task_queue.task_done()
    
    print("[Thread 2] Shutdown signal received. Exiting.")