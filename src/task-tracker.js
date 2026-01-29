/**
 * TaskTracker Web Component
 *
 * A simple task management component demonstrating:
 * - Web Components (Shadow DOM, Custom Elements)
 * - Event handling
 * - State management
 * - TDD workflow
 *
 * Features:
 * - Add tasks with input field
 * - Mark tasks as complete (checkbox)
 * - Delete tasks
 * - Task counter (total and completed)
 *
 * @example
 * <task-tracker></task-tracker>
 */

class TaskTracker extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.tasks = [];
  }

  connectedCallback() {
    this.render();
    this.attachEventListeners();
  }

  /**
   * Render the component's HTML and CSS
   */
  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          max-width: 600px;
          margin: 0 auto;
          padding: 20px;
        }

        .header {
          margin-bottom: 20px;
        }

        h2 {
          margin: 0 0 10px 0;
          color: #333;
        }

        .input-container {
          display: flex;
          gap: 10px;
          margin-bottom: 20px;
        }

        input[type="text"] {
          flex: 1;
          padding: 12px;
          border: 2px solid #e0e0e0;
          border-radius: 6px;
          font-size: 14px;
          transition: border-color 0.2s;
        }

        input[type="text"]:focus {
          outline: none;
          border-color: #4CAF50;
        }

        button {
          padding: 12px 24px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        button.add-btn {
          background: #4CAF50;
          color: white;
        }

        button.add-btn:hover {
          background: #45a049;
        }

        button.add-btn:active {
          transform: scale(0.98);
        }

        .task-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .task-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          margin-bottom: 8px;
          background: #f9f9f9;
          border-radius: 6px;
          transition: all 0.2s;
        }

        .task-item:hover {
          background: #f0f0f0;
        }

        .task-item.completed {
          opacity: 0.6;
        }

        .task-item.completed .task-text {
          text-decoration: line-through;
          color: #999;
        }

        input[type="checkbox"] {
          width: 20px;
          height: 20px;
          cursor: pointer;
        }

        .task-text {
          flex: 1;
          font-size: 14px;
          color: #333;
        }

        button.delete-btn {
          background: #f44336;
          color: white;
          padding: 6px 12px;
          font-size: 12px;
        }

        button.delete-btn:hover {
          background: #da190b;
        }

        .task-counter {
          margin-top: 20px;
          padding: 12px;
          background: #e3f2fd;
          border-radius: 6px;
          font-size: 14px;
          color: #1976d2;
          text-align: center;
        }

        .empty-state {
          text-align: center;
          padding: 40px 20px;
          color: #999;
        }
      </style>

      <div class="header">
        <h2>Task Tracker</h2>
      </div>

      <div class="input-container">
        <input
          type="text"
          placeholder="Add a new task..."
          data-testid="task-input"
        />
        <button class="add-btn" data-testid="add-button">Add</button>
      </div>

      <ul class="task-list" data-testid="task-list"></ul>

      <div class="task-counter" data-testid="task-counter"></div>
    `;

    this.updateTaskList();
  }

  /**
   * Attach event listeners to input and button
   */
  attachEventListeners() {
    const input = this.shadowRoot.querySelector('input[type="text"]');
    const button = this.shadowRoot.querySelector('button.add-btn');

    button.addEventListener('click', () => this.addTask());

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.addTask();
      }
    });
  }

  /**
   * Add a new task to the list
   */
  addTask() {
    const input = this.shadowRoot.querySelector('input[type="text"]');
    const text = input.value.trim();

    if (text === '') {
      return;
    }

    this.tasks.push({
      id: Date.now(),
      text: text,
      completed: false
    });

    input.value = '';
    this.updateTaskList();
  }

  /**
   * Toggle task completion status
   * @param {number} id - Task ID
   */
  toggleTask(id) {
    const task = this.tasks.find(t => t.id === id);
    if (task) {
      task.completed = !task.completed;
      this.updateTaskList();
    }
  }

  /**
   * Delete a task
   * @param {number} id - Task ID
   */
  deleteTask(id) {
    this.tasks = this.tasks.filter(t => t.id !== id);
    this.updateTaskList();
  }

  /**
   * Update the task list UI
   */
  updateTaskList() {
    const list = this.shadowRoot.querySelector('.task-list');
    const counter = this.shadowRoot.querySelector('.task-counter');

    // Clear existing tasks
    list.innerHTML = '';

    if (this.tasks.length === 0) {
      list.innerHTML = '<li class="empty-state">No tasks yet. Add one above!</li>';
      counter.textContent = 'No tasks';
      return;
    }

    // Render tasks
    this.tasks.forEach(task => {
      const li = document.createElement('li');
      li.className = `task-item ${task.completed ? 'completed' : ''}`;
      li.innerHTML = `
        <input
          type="checkbox"
          ${task.completed ? 'checked' : ''}
          data-id="${task.id}"
        />
        <span class="task-text">${this.escapeHtml(task.text)}</span>
        <button class="delete-btn" data-id="${task.id}">Delete</button>
      `;

      // Add event listeners
      const checkbox = li.querySelector('input[type="checkbox"]');
      checkbox.addEventListener('click', () => this.toggleTask(task.id));

      const deleteBtn = li.querySelector('button.delete-btn');
      deleteBtn.addEventListener('click', () => this.deleteTask(task.id));

      list.appendChild(li);
    });

    // Update counter
    const completed = this.tasks.filter(t => t.completed).length;
    const total = this.tasks.length;

    if (completed === 0) {
      counter.textContent = `${total} ${total === 1 ? 'task' : 'tasks'}`;
    } else {
      counter.textContent = `${completed} of ${total} completed`;
    }
  }

  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Export for Node.js (Jest)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TaskTracker;
}

// Register for browser (if not already registered)
if (typeof customElements !== 'undefined' && !customElements.get('task-tracker')) {
  customElements.define('task-tracker', TaskTracker);
}
