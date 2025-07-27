#!/usr/bin/env python3
"""
Simple To-Do List Application
A beginner-friendly command-line to-do list manager

Features:
- Add new tasks
- View all tasks
- Mark tasks as completed
- Delete tasks
- Save tasks to file

Author: Your Name
License: MIT
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

class TodoList:
    def __init__(self, filename="tasks.json"):
        self.filename = filename
        self.tasks: List[Dict] = self.load_tasks()
        self.task_index: Dict[str, Dict] = {task["id"]: task for task in self.tasks}
        self._dirty = False

    def load_tasks(self):
        """Load tasks from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print("Error: 任务文件已损坏，创建新的任务列表")
                return []
        return []

    def save_tasks(self):
        """Save tasks to file only if changes were made"""
        if not self._dirty:
            return
        try:
            with open(self.filename, 'w', encoding='utf-8') as file:
                json.dump(self.tasks, file, ensure_ascii=False, indent=2)
            self._dirty = False
        except Exception as e:
            print(f"保存任务时出错: {e}")

    def _mark_dirty(self):
        """Mark that changes need to be saved"""
        self._dirty = True

    def add_task(self, description: str) -> bool:
        """Add a new task"""
        if not description or not description.strip():
            print("❌ 任务描述不能为空")
            return False
            
        task_id = str(uuid.uuid4())[:8]
        task = {
            "id": task_id,
            "description": description.strip(),
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.tasks.append(task)
        self.task_index[task_id] = task
        self._mark_dirty()
        self.save_tasks()
        print(f"✅ 任务已添加: {description}")
        return True

    def view_tasks(self):
        """Display all tasks"""
        if not self.tasks:
            print("📝 暂无任务")
            return

        print("\n📋 任务列表:")
        print("-" * 50)
        for i, task in enumerate(self.tasks, 1):
            status = "✅" if task["completed"] else "⏳"
            print(f"{status} [{i}] {task['description']} (ID: {task['id'][:6]})")
            print(f"   创建时间: {task['created_at']}")
        print("-" * 50)

    def _find_task_by_number(self, display_number: int) -> Optional[Dict]:
        """Find task by display number (1-indexed)"""
        if 1 <= display_number <= len(self.tasks):
            return self.tasks[display_number - 1]
        return None

    def complete_task(self, task_number: int) -> bool:
        """Mark a task as completed using display number"""
        task = self._find_task_by_number(task_number)
        if not task:
            print(f"❌ 未找到编号为 {task_number} 的任务")
            return False
            
        if task["completed"]:
            print(f"❌ 任务 {task_number} 已经完成了")
            return False
        else:
            task["completed"] = True
            task["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._mark_dirty()
            self.save_tasks()
            print(f"🎉 任务 {task_number} 已标记为完成!")
            return True

    def delete_task(self, task_number: int) -> bool:
        """Delete a task using display number"""
        task = self._find_task_by_number(task_number)
        if not task:
            print(f"❌ 未找到编号为 {task_number} 的任务")
            return False
            
        # Remove from index and list
        del self.task_index[task["id"]]
        self.tasks.remove(task)
        self._mark_dirty()
        self.save_tasks()
        print(f"🗑️ 任务已删除: {task['description']}")
        return True

def safe_input(prompt: str, input_type=str, validator=None):
    """Safe input with type validation"""
    while True:
        try:
            user_input = input(prompt).strip()
            if not user_input:
                if input_type == str:
                    return None
                else:
                    print("❌ 输入不能为空，请重试")
                    continue
                    
            converted_input = input_type(user_input)
            
            if validator and not validator(converted_input):
                print("❌ 输入无效，请重试")
                continue
                
            return converted_input
        except ValueError:
            print(f"❌ 请输入有效的{input_type.__name__}类型")
        except KeyboardInterrupt:
            print("\n👋 操作已取消")
            return None

def display_menu():
    """Display the main menu"""
    print("\n" + "="*30)
    print("🚀 简单任务管理器 v1.0")
    print("="*30)
    print("1. ➕ 添加任务")
    print("2. 📋 查看所有任务")
    print("3. ✅ 完成任务")
    print("4. 🗑️ 删除任务")
    print("5. 🚪 退出")
    print("="*30)

def main():
    """Main program loop"""
    import sys
    if sys.platform == "win32":
        import os
        os.system("chcp 65001 >nul")
    
    todo = TodoList()

    print("欢迎使用简单任务管理器!")

    while True:
        display_menu()
        choice = safe_input("请选择操作 (1-5): ", str, lambda x: x in "12345")
        
        if choice is None:
            continue

        if choice == "1":
            description = safe_input("输入新任务: ")
            if description:
                todo.add_task(description)

        elif choice == "2":
            todo.view_tasks()

        elif choice == "3":
            if not todo.tasks:
                print("没有可完成的任务")
                continue
            task_number = safe_input("输入要完成的任务编号: ", int, 
                                   lambda x: 1 <= x <= len(todo.tasks))
            if task_number is not None:
                todo.complete_task(task_number)

        elif choice == "4":
            if not todo.tasks:
                print("没有可删除的任务")
                continue
            task_number = safe_input("输入要删除的任务编号: ", int,
                                   lambda x: 1 <= x <= len(todo.tasks))
            if task_number is not None:
                todo.delete_task(task_number)

        elif choice == "5":
            # Save any pending changes before exit
            todo.save_tasks()
            print("再见! 感谢使用任务管理器!")
            break

if __name__ == "__main__":
    main()
