import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Railway/Heroku fix for PostgreSQL URL
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    priority = db.Column(db.String(10), default='normal', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def complete(self):
        self.completed = True
        db.session.commit()
    
    def __str__(self):
        status = "✓" if self.completed else "○"
        priority_icon = "🔥" if self.priority == 'high' else "⭐" if self.priority == 'normal' else "💤"
        return f"{status} {priority_icon} {self.title}"
    
    def __repr__(self):
        return f"Task('{self.title}', completed={self.completed}, priority='{self.priority}')"
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.isoformat(),
            'priority': self.priority
        }

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form.get('title', '').strip()
    priority = request.form.get('priority', 'normal')
    
    if title:
        new_task = Task(title=title, priority=priority)
        db.session.add(new_task)
        db.session.commit()
        flash(f'Task "{title}" added successfully!', 'success')
    else:
        flash('Task title cannot be empty!', 'error')
    
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.complete()
    flash(f'Task "{task.title}" completed!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    title = task.title
    db.session.delete(task)
    db.session.commit()
    flash(f'Task "{title}" deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/stats')
def stats():
    total = Task.query.count()
    completed = Task.query.filter_by(completed=True).count()
    pending = total - completed
    
    high_priority = Task.query.filter_by(priority='high').count()
    normal_priority = Task.query.filter_by(priority='normal').count()
    low_priority = Task.query.filter_by(priority='low').count()
    
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
    tasks = Task.query.all()
    return jsonify({
        'tasks': [task.to_dict() for task in tasks],
        'count': len(tasks),
        'summary': {
            'completed': Task.query.filter_by(completed=True).count(),
            'pending': Task.query.filter_by(completed=False).count()
        }
    })

@app.route('/filter/<status>')
def filter_tasks(status):
    if status == 'completed':
        tasks = Task.query.filter_by(completed=True).all()
        title = "Completed Tasks"
    elif status == 'pending':
        tasks = Task.query.filter_by(completed=False).all()
        title = "Pending Tasks"
    elif status == 'high':
        tasks = Task.query.filter_by(priority='high').all()
        title = "High Priority Tasks"
    else:
        tasks = Task.query.all()
        title = "All Tasks"
    
    return render_template('index.html', tasks=tasks, page_title=title)

@app.route('/debug/db')
def debug_db():
    """Debug endpoint to check database connection"""
    try:
        # Check database connection with a simple query
        db.session.execute(db.text('SELECT 1')).fetchone()
        
        # Get table info (updated for newer SQLAlchemy)
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Count tasks
        task_count = Task.query.count()
        
        # Get database URL (hide password)
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        if '@' in db_url:
            # Hide password: postgresql://user:password@host/db -> host/db
            safe_url = db_url.split('@')[-1]
            db_type = 'PostgreSQL'
        else:
            safe_url = 'SQLite local file'
            db_type = 'SQLite'
        
        return jsonify({
            'database_connected': True,
            'database_type': db_type,
            'database_host': safe_url,
            'tables': tables,
            'task_count': task_count,
            'recent_tasks': [task.to_dict() for task in Task.query.limit(5).all()]
        })
    except Exception as e:
        return jsonify({
            'database_connected': False,
            'error': str(e),
            'database_url_configured': bool(os.environ.get('DATABASE_URL')),
            'sqlalchemy_uri': app.config['SQLALCHEMY_DATABASE_URI'][:50] + '...' if len(app.config['SQLALCHEMY_DATABASE_URI']) > 50 else app.config['SQLALCHEMY_DATABASE_URI']
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)