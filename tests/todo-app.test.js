/**
 * Tests for TodoApp
 * Uses custom DOM mocks (no jsdom required)
 */

// Mock DOM elements and localStorage before importing TodoApp
let mockLocalStorage = {};

// Create mock element factory
function createMockElement(tagName) {
  const children = [];
  const eventListeners = {};
  const element = {
    tagName: tagName.toUpperCase(),
    className: '',
    classList: {
      add: function(cls) {
        if (!element.className.includes(cls)) {
          element.className = element.className ? element.className + ' ' + cls : cls;
        }
      },
      remove: function(cls) {
        element.className = element.className.replace(new RegExp('\\b' + cls + '\\b', 'g'), '').trim();
      },
      contains: function(cls) {
        return element.className.split(' ').includes(cls);
      },
      toggle: function(cls) {
        if (element.classList.contains(cls)) {
          element.classList.remove(cls);
          return false;
        } else {
          element.classList.add(cls);
          return true;
        }
      }
    },
    innerHTML: '',
    textContent: '',
    value: '',
    type: '',
    placeholder: '',
    checked: false,
    children: children,
    appendChild: function(child) {
      children.push(child);
      child.parentNode = element;
      return child;
    },
    removeChild: function(child) {
      const idx = children.indexOf(child);
      if (idx > -1) children.splice(idx, 1);
      child.parentNode = null;
      return child;
    },
    parentNode: null,
    addEventListener: function(event, handler) {
      if (!eventListeners[event]) eventListeners[event] = [];
      eventListeners[event].push(handler);
    },
    removeEventListener: function() {},
    dispatchEvent: function(event) {
      const handlers = eventListeners[event.type] || [];
      handlers.forEach(h => h(event));
    },
    click: function() {
      this.dispatchEvent({ type: 'click', target: this });
    },
    querySelector: function(selector) {
      return findInChildren(children, selector);
    },
    querySelectorAll: function(selector) {
      return findAllInChildren(children, selector);
    },
    focus: function() {},
    blur: function() {}
  };
  return element;
}

// Helper to find elements by selector
function findInChildren(children, selector) {
  for (const child of children) {
    if (matchesSelector(child, selector)) return child;
    if (child.children) {
      const found = findInChildren(child.children, selector);
      if (found) return found;
    }
  }
  return null;
}

function findAllInChildren(children, selector) {
  const results = [];
  for (const child of children) {
    if (matchesSelector(child, selector)) results.push(child);
    if (child.children) {
      results.push(...findAllInChildren(child.children, selector));
    }
  }
  return results;
}

function matchesSelector(element, selector) {
  if (!element || !element.tagName) return false;

  // Handle multiple selectors (comma-separated)
  const selectors = selector.split(',').map(s => s.trim());

  for (const sel of selectors) {
    // Class selector
    if (sel.startsWith('.')) {
      if (element.className && element.className.includes(sel.slice(1))) return true;
    }
    // Attribute selector
    else if (sel.includes('[')) {
      const match = sel.match(/(\w+)?\[([^\]=]+)(?:="([^"]+)")?\]/);
      if (match) {
        const [, tag, attr, value] = match;
        if (tag && element.tagName.toLowerCase() !== tag.toLowerCase()) continue;
        if (attr === 'type' && element.type === value) return true;
        if (attr === 'class' && element.className.includes(value)) return true;
      }
    }
    // Combined selector (tag.class)
    else if (sel.includes('.')) {
      const [tag, cls] = sel.split('.');
      if (element.tagName.toLowerCase() === tag.toLowerCase() &&
          element.className && element.className.includes(cls)) {
        return true;
      }
    }
    // Tag selector
    else if (element.tagName.toLowerCase() === sel.toLowerCase()) {
      return true;
    }
  }
  return false;
}

// Set up global mocks
global.localStorage = {
  getItem: jest.fn((key) => mockLocalStorage[key] || null),
  setItem: jest.fn((key, value) => { mockLocalStorage[key] = value; }),
  removeItem: jest.fn((key) => { delete mockLocalStorage[key]; }),
  clear: jest.fn(() => { mockLocalStorage = {}; })
};

global.document = {
  createElement: jest.fn((tagName) => createMockElement(tagName))
};

// Now require the TodoApp
const { TodoApp } = require('../src/todo-app.js');

describe('TodoApp', () => {
  let container;
  let todoApp;

  beforeEach(() => {
    // Reset localStorage mock
    mockLocalStorage = {};
    jest.clearAllMocks();

    // Create mock container
    container = createMockElement('div');
    container.id = 'app';

    // Initialize the app (stored for potential future tests)
    todoApp = new TodoApp(container);
    void todoApp; // Mark as intentionally unused
  });

  afterEach(() => {
    mockLocalStorage = {};
  });

  describe('Initialization', () => {
    test('should render input field for adding todos', () => {
      const input = container.querySelector('input[type="text"]');
      expect(input).not.toBeNull();
      expect(input.placeholder.toLowerCase()).toContain('todo');
    });

    test('should render add button', () => {
      const addButton = container.querySelector('.add-btn');
      expect(addButton).not.toBeNull();
    });

    test('should render empty todo list container', () => {
      const todoList = container.querySelector('.todo-list');
      expect(todoList).not.toBeNull();
    });
  });

  describe('Adding Todos', () => {
    test('should add a new todo when clicking add button', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Buy groceries';
      addButton.click();

      const todoItems = container.querySelectorAll('.todo-item');
      expect(todoItems.length).toBe(1);
    });

    test('should add a new todo when pressing Enter', () => {
      const input = container.querySelector('input[type="text"]');

      input.value = 'Walk the dog';
      input.dispatchEvent({ type: 'keypress', key: 'Enter' });

      const todoItems = container.querySelectorAll('.todo-item');
      expect(todoItems.length).toBe(1);
    });

    test('should clear input after adding todo', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Test todo';
      addButton.click();

      expect(input.value).toBe('');
    });

    test('should not add empty todos', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = '   ';
      addButton.click();

      const todoItems = container.querySelectorAll('.todo-item');
      expect(todoItems.length).toBe(0);
    });

    test('should add multiple todos', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Todo 1';
      addButton.click();

      input.value = 'Todo 2';
      addButton.click();

      input.value = 'Todo 3';
      addButton.click();

      const todoItems = container.querySelectorAll('.todo-item');
      expect(todoItems.length).toBe(3);
    });
  });

  describe('Completing Todos', () => {
    test('should toggle todo completion when clicking checkbox', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Complete me';
      addButton.click();

      const checkbox = container.querySelector('input[type="checkbox"]');
      expect(checkbox.checked).toBe(false);

      checkbox.click();
      expect(checkbox.checked).toBe(true);
    });

    test('should toggle todo back to incomplete', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Toggle me';
      addButton.click();

      const checkbox = container.querySelector('input[type="checkbox"]');
      checkbox.click(); // Complete
      checkbox.click(); // Incomplete

      expect(checkbox.checked).toBe(false);
    });
  });

  describe('Deleting Todos', () => {
    test('should delete todo when clicking delete button', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Delete me';
      addButton.click();

      let todoItems = container.querySelectorAll('.todo-item');
      expect(todoItems.length).toBe(1);

      const deleteButton = container.querySelector('.delete-btn');
      deleteButton.click();

      todoItems = container.querySelectorAll('.todo-item');
      expect(todoItems.length).toBe(0);
    });

    test('should only delete the specific todo', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Todo 1';
      addButton.click();

      input.value = 'Todo 2';
      addButton.click();

      input.value = 'Todo 3';
      addButton.click();

      const deleteButtons = container.querySelectorAll('.delete-btn');
      deleteButtons[1].click(); // Delete middle todo

      const todoItems = container.querySelectorAll('.todo-item');
      expect(todoItems.length).toBe(2);
    });
  });

  describe('LocalStorage Persistence', () => {
    test('should save todos to localStorage', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Persistent todo';
      addButton.click();

      expect(localStorage.setItem).toHaveBeenCalled();
      const stored = JSON.parse(mockLocalStorage['todos']);
      expect(stored).not.toBeNull();
      expect(stored.length).toBe(1);
      expect(stored[0].text).toBe('Persistent todo');
    });

    test('should load todos from localStorage on init', () => {
      // Pre-populate localStorage
      const existingTodos = [
        { id: 1, text: 'Existing todo 1', completed: false },
        { id: 2, text: 'Existing todo 2', completed: true }
      ];
      mockLocalStorage['todos'] = JSON.stringify(existingTodos);

      // Create new instance (simulating page refresh)
      const newContainer = createMockElement('div');
      new TodoApp(newContainer);

      const todoItems = newContainer.querySelectorAll('.todo-item');
      expect(todoItems.length).toBe(2);
    });

    test('should update localStorage when completing a todo', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Complete and save';
      addButton.click();

      const checkbox = container.querySelector('input[type="checkbox"]');
      checkbox.click();

      const stored = JSON.parse(mockLocalStorage['todos']);
      expect(stored[0].completed).toBe(true);
    });

    test('should update localStorage when deleting a todo', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Delete and save';
      addButton.click();

      const deleteButton = container.querySelector('.delete-btn');
      deleteButton.click();

      const stored = JSON.parse(mockLocalStorage['todos']);
      expect(stored.length).toBe(0);
    });
  });

  describe('Display', () => {
    test('should have all UI elements for each todo item', () => {
      const input = container.querySelector('input[type="text"]');
      const addButton = container.querySelector('.add-btn');

      input.value = 'Check UI elements';
      addButton.click();

      const todoItem = container.querySelector('.todo-item');
      expect(todoItem).not.toBeNull();
      expect(container.querySelector('input[type="checkbox"]')).not.toBeNull();
      expect(container.querySelector('.todo-text')).not.toBeNull();
      expect(container.querySelector('.delete-btn')).not.toBeNull();
    });
  });
});
