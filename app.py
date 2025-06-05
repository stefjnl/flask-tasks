import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

class Task:
    def __init__(self, title, priority='normal'):
        self.title = title
        self.completed = False
        self.created_at = datetime.now()
        self.priority = priority

    def complete(self):
        self.completed = True

    def __str__(self):
        status = "✓" if self.completed else "○"
        priority_icon = "🔥" if self.priority == 'high' else "⭐" if self.priority == 'normal' else "💤"
        return f"{status} {priority_icon} {self.title}"

    def __repr__(self):
        return f"Task('{self.title}', completed={self.completed}, priority='{self.priority}')"

    def to_dict(self):
        return {
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.isoformat(),
            'priority': self.priority
        }

# In-memory storage
tasks = []

@app.route('/')
def index():
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form.get('title', '').strip()
    priority = request.form.get('priority', 'normal')
    
    if title:
        new_task = Task(title, priority)
        tasks.append(new_task)
        flash(f'Task "{title}" added successfully!', 'success')
    else:
        flash('Task title cannot be empty!', 'error')
    
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    if 0 <= task_id < len(tasks):
        tasks[task_id].complete()
        flash(f'Task "{tasks[task_id].title}" completed!', 'success')
    else:
        flash('Task not found!', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 0 <= task_id < len(tasks):
        deleted_task = tasks.pop(task_id)
        flash(f'Task "{deleted_task.title}" deleted!', 'success')
    else:
        flash('Task not found!', 'error')
    
    return redirect(url_for('index'))

@app.route('/stats')
def stats():
    total = len(tasks)
    completed = sum(1 for task in tasks if task.completed)
    pending = total - completed
    
    high_priority = len([t for t in tasks if t.priority == 'high'])
    normal_priority = len([t for t in tasks if t.priority == 'normal'])
    low_priority = len([t for t in tasks if t.priority == 'low'])
    
    stats_data = {
        'total': total,
        'completed': completed,
        'pending': pending,
        'completion_rate': round((completed / total * 100) if total > 0 else 0, 1),
        'high_priority': high_priority,
        'normal_priority': normal_priority,
        'low_priority': low_priority
    }
    
    return render_template('stats.html', stats=stats_data)

@app.route('/api/tasks')
def api_tasks():
    return jsonify({
        'tasks': [task.to_dict() for task in tasks],
        'count': len(tasks),
        'summary': {
            'completed': sum(1 for t in tasks if t.completed),
            'pending': sum(1 for t in tasks if not t.completed)
        }
    })

@app.route('/filter/<status>')
def filter_tasks(status):
    if status == 'completed':
        filtered_tasks = [task for task in tasks if task.completed]
        title = "Completed Tasks"
    elif status == 'pending':
        filtered_tasks = [task for task in tasks if not task.completed]
        title = "Pending Tasks"
    elif status == 'high':
        filtered_tasks = [task for task in tasks if task.priority == 'high']
        title = "High Priority Tasks"
    else:
        filtered_tasks = tasks
        title = "All Tasks"
    
    return render_template('index.html', tasks=filtered_tasks, page_title=title)

if __name__ == '__main__':
    # Railway automatically sets PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)