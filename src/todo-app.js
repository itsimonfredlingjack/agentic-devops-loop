/**
 * TodoApp - A simple todo list application
 * Supports adding, completing, and deleting todos with localStorage persistence
 */

class TodoApp {
  constructor(container) {
    this.container = container;
    this.todos = [];
    this.nextId = 1;

    this.loadFromStorage();
    this.render();
    this.attachEventListeners();
  }

  /**
   * Load todos from localStorage
   */
  loadFromStorage() {
    const stored = localStorage.getItem('todos');
    if (stored) {
      try {
        this.todos = JSON.parse(stored);
        // Find the highest ID to continue from there
        this.nextId = this.todos.reduce((max, todo) => Math.max(max, todo.id + 1), 1);
      } catch {
        this.todos = [];
      }
    }
  }

  /**
   * Save todos to localStorage
   */
  saveToStorage() {
    localStorage.setItem('todos', JSON.stringify(this.todos));
  }

  /**
   * Render the todo app UI
   */
  render() {
    // Clear container
    this.container.children.length = 0;

    // Create input container
    const inputContainer = document.createElement('div');
    inputContainer.className = 'input-container';
    this.container.appendChild(inputContainer);

    // Create input field
    this.inputField = document.createElement('input');
    this.inputField.type = 'text';
    this.inputField.placeholder = 'Add a new todo...';
    this.inputField.className = 'todo-input';
    inputContainer.appendChild(this.inputField);

    // Create add button
    this.addButton = document.createElement('button');
    this.addButton.textContent = 'Add';
    this.addButton.className = 'add-btn';
    inputContainer.appendChild(this.addButton);

    // Create todo list container
    this.todoList = document.createElement('div');
    this.todoList.className = 'todo-list';
    this.container.appendChild(this.todoList);

    // Render existing todos
    this.renderTodos();
  }

  /**
   * Render all todo items
   */
  renderTodos() {
    // Clear existing items
    this.todoList.children.length = 0;

    // Render each todo
    this.todos.forEach(todo => {
      const todoItem = this.createTodoElement(todo);
      this.todoList.appendChild(todoItem);
    });
  }

  /**
   * Create a DOM element for a todo item
   */
  createTodoElement(todo) {
    const todoItem = document.createElement('div');
    todoItem.className = todo.completed ? 'todo-item completed' : 'todo-item';
    todoItem.dataset = { id: todo.id };

    // Checkbox
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = todo.completed;
    checkbox.className = 'todo-checkbox';
    checkbox.addEventListener('click', () => this.toggleTodo(todo.id));
    todoItem.appendChild(checkbox);

    // Todo text
    const todoText = document.createElement('span');
    todoText.textContent = todo.text;
    todoText.className = 'todo-text';
    todoItem.appendChild(todoText);

    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.className = 'delete-btn';
    deleteBtn.addEventListener('click', () => this.deleteTodo(todo.id));
    todoItem.appendChild(deleteBtn);

    return todoItem;
  }

  /**
   * Attach event listeners for input and add button
   */
  attachEventListeners() {
    this.addButton.addEventListener('click', () => this.addTodo());

    this.inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.addTodo();
      }
    });
  }

  /**
   * Add a new todo
   */
  addTodo() {
    const text = this.inputField.value.trim();

    if (!text) {
      return;
    }

    const todo = {
      id: this.nextId++,
      text: text,
      completed: false
    };

    this.todos.push(todo);
    this.saveToStorage();

    // Add to DOM
    const todoItem = this.createTodoElement(todo);
    this.todoList.appendChild(todoItem);

    // Clear input
    this.inputField.value = '';
  }

  /**
   * Toggle todo completion status
   */
  toggleTodo(id) {
    const todo = this.todos.find(t => t.id === id);
    if (todo) {
      todo.completed = !todo.completed;
      this.saveToStorage();

      // Update DOM - find the checkbox and toggle it
      const todoItems = this.todoList.querySelectorAll('.todo-item');
      todoItems.forEach(item => {
        if (item.dataset && item.dataset.id === id) {
          const checkbox = item.querySelector('input[type="checkbox"]');
          if (checkbox) {
            checkbox.checked = todo.completed;
          }
          item.classList.toggle('completed');
        }
      });
    }
  }

  /**
   * Delete a todo
   */
  deleteTodo(id) {
    const index = this.todos.findIndex(t => t.id === id);
    if (index > -1) {
      this.todos.splice(index, 1);
      this.saveToStorage();

      // Remove from DOM
      const todoItems = Array.from(this.todoList.querySelectorAll('.todo-item'));
      if (todoItems[index]) {
        this.todoList.removeChild(todoItems[index]);
      }
    }
  }
}

// Export for CommonJS (Node.js/Jest) and browser
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TodoApp };
}
