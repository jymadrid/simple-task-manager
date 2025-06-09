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
from datetime import datetime

class TodoList:
    def __init__(self, filename="tasks.json"):
        self.filename = filename
        self.tasks = self.load_tasks()

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
        """Save tasks to file"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as file:
                json.dump(self.tasks, file, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务时出错: {e}")

    def add_task(self, description):
        """Add a new task"""
        task = {
            "id": len(self.tasks) + 1,
            "description": description,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.tasks.append(task)
        self.save_tasks()
        print(f"✅ 任务已添加: {description}")

    def view_tasks(self):
        """Display all tasks"""
        if not self.tasks:
            print("📝 暂无任务")
            return

        print("\n📋 任务列表:")
        print("-" * 50)
        for task in self.tasks:
            status = "✅" if task["completed"] else "⏳"
            print(f"{status} [{task['id']}] {task['description']}")
            print(f"   创建时间: {task['created_at']}")
        print("-" * 50)

    def complete_task(self, task_id):
        """Mark a task as completed"""
        for task in self.tasks:
            if task["id"] == task_id:
                if task["completed"]:
                    print(f"❌ 任务 {task_id} 已经完成了")
                else:
                    task["completed"] = True
                    task["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.save_tasks()
                    print(f"🎉 任务 {task_id} 已标记为完成!")
                return
        print(f"❌ 未找到ID为 {task_id} 的任务")

    def delete_task(self, task_id):
        """Delete a task"""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                deleted_task = self.tasks.pop(i)
                # Reorder task IDs
                for j, remaining_task in enumerate(self.tasks[i:], start=i):
                    remaining_task["id"] = j + 1
                self.save_tasks()
                print(f"🗑️ 任务已删除: {deleted_task['description']}")
                return
        print(f"❌ 未找到ID为 {task_id} 的任务")

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
    todo = TodoList()

    print("欢迎使用简单任务管理器! 🎯")

    while True:
        display_menu()
        choice = input("请选择操作 (1-5): ").strip()

        if choice == "1":
            description = input("输入新任务: ").strip()
            if description:
                todo.add_task(description)
            else:
                print("❌ 任务描述不能为空")

        elif choice == "2":
            todo.view_tasks()

        elif choice == "3":
            try:
                task_id = int(input("输入要完成的任务ID: "))
                todo.complete_task(task_id)
            except ValueError:
                print("❌ 请输入有效的数字ID")

        elif choice == "4":
            try:
                task_id = int(input("输入要删除的任务ID: "))
                todo.delete_task(task_id)
            except ValueError:
                print("❌ 请输入有效的数字ID")

        elif choice == "5":
            print("👋 再见! 感谢使用任务管理器!")
            break

        else:
            print("❌ 无效选择，请输入1-5之间的数字")

if __name__ == "__main__":
    main()
