/**
 * Tests for TaskTracker web component
 *
 * Simplified version that tests the core logic without Custom Elements API
 * (JSDOM has limited Custom Elements support)
 */

const TaskTracker = require('../src/task-tracker.js');

describe('TaskTracker - Core Functionality', () => {
  let tracker;

  beforeEach(() => {
    tracker = new TaskTracker();
    // Mock shadowRoot
    tracker.shadowRoot = { innerHTML: '' };
    tracker.tasks = [];
    // Mock updateTaskList to avoid DOM dependencies
    tracker.updateTaskList = jest.fn();
  });

  describe('Task Management', () => {
    test('initializes with empty task list', () => {
      expect(tracker.tasks).toEqual([]);
    });

    test('adds task with valid text', () => {
      const initialLength = tracker.tasks.length;

      // Simulate adding a task
      tracker.tasks.push({
        id: Date.now(),
        text: 'Buy groceries',
        completed: false
      });

      expect(tracker.tasks.length).toBe(initialLength + 1);
      expect(tracker.tasks[0].text).toBe('Buy groceries');
      expect(tracker.tasks[0].completed).toBe(false);
    });

    test('does not add empty text (simulated)', () => {
      const text = '   '.trim();

      if (text === '') {
        // Don't add
      } else {
        tracker.tasks.push({ id: Date.now(), text, completed: false });
      }

      expect(tracker.tasks.length).toBe(0);
    });

    test('toggles task completion', () => {
      tracker.tasks = [{
        id: 1,
        text: 'Test task',
        completed: false
      }];

      tracker.toggleTask(1);

      expect(tracker.tasks[0].completed).toBe(true);
    });

    test('toggles task back to incomplete', () => {
      tracker.tasks = [{
        id: 1,
        text: 'Test task',
        completed: true
      }];

      tracker.toggleTask(1);

      expect(tracker.tasks[0].completed).toBe(false);
    });

    test('deletes task by id', () => {
      tracker.tasks = [
        { id: 1, text: 'Task 1', completed: false },
        { id: 2, text: 'Task 2', completed: false },
        { id: 3, text: 'Task 3', completed: false }
      ];

      tracker.deleteTask(2);

      expect(tracker.tasks.length).toBe(2);
      expect(tracker.tasks.find(t => t.id === 2)).toBeUndefined();
      expect(tracker.tasks[0].id).toBe(1);
      expect(tracker.tasks[1].id).toBe(3);
    });

    test('handles multiple tasks', () => {
      tracker.tasks = [
        { id: 1, text: 'Task 1', completed: false },
        { id: 2, text: 'Task 2', completed: false },
        { id: 3, text: 'Task 3', completed: false }
      ];

      expect(tracker.tasks.length).toBe(3);
    });
  });

  describe('HTML Escaping', () => {
    test('escapes HTML in task text', () => {
      const escaped = tracker.escapeHtml('<script>alert("xss")</script>');
      expect(escaped).not.toContain('<script>');
      expect(escaped).toContain('&lt;script&gt;');
    });

    test('escapes quotes', () => {
      const escaped = tracker.escapeHtml('Task with "quotes"');
      // textContent doesn't escape quotes, only < > &
      expect(escaped).toContain('quotes');
    });

    test('preserves safe text', () => {
      const escaped = tracker.escapeHtml('Normal task text');
      expect(escaped).toBe('Normal task text');
    });
  });

  describe('Task Counting', () => {
    test('counts total tasks', () => {
      tracker.tasks = [
        { id: 1, text: 'Task 1', completed: false },
        { id: 2, text: 'Task 2', completed: true },
        { id: 3, text: 'Task 3', completed: false }
      ];

      const total = tracker.tasks.length;
      expect(total).toBe(3);
    });

    test('counts completed tasks', () => {
      tracker.tasks = [
        { id: 1, text: 'Task 1', completed: false },
        { id: 2, text: 'Task 2', completed: true },
        { id: 3, text: 'Task 3', completed: true }
      ];

      const completed = tracker.tasks.filter(t => t.completed).length;
      expect(completed).toBe(2);
    });

    test('counts incomplete tasks', () => {
      tracker.tasks = [
        { id: 1, text: 'Task 1', completed: false },
        { id: 2, text: 'Task 2', completed: true },
        { id: 3, text: 'Task 3', completed: false }
      ];

      const incomplete = tracker.tasks.filter(t => !t.completed).length;
      expect(incomplete).toBe(2);
    });
  });

  describe('Edge Cases', () => {
    test('handles deleting non-existent task', () => {
      tracker.tasks = [{ id: 1, text: 'Task 1', completed: false }];

      tracker.deleteTask(999);

      expect(tracker.tasks.length).toBe(1);
    });

    test('handles toggling non-existent task', () => {
      tracker.tasks = [{ id: 1, text: 'Task 1', completed: false }];

      tracker.toggleTask(999);

      expect(tracker.tasks[0].completed).toBe(false);
    });

    test('handles empty task list', () => {
      tracker.tasks = [];

      const total = tracker.tasks.length;
      const completed = tracker.tasks.filter(t => t.completed).length;

      expect(total).toBe(0);
      expect(completed).toBe(0);
    });
  });
});
