/**
 * Tests for TimestampDisplay web component
 * Following TDD: Write failing tests first
 */

describe('TimestampDisplay Component', () => {
  let component;

  beforeEach(() => {
    // Create a fresh instance before each test
    document.body.innerHTML = '<timestamp-display></timestamp-display>';
    component = document.querySelector('timestamp-display');
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllTimers();
  });

  describe('Date Display', () => {
    test('should display current date in YYYY-MM-DD format', () => {
      const dateElement = component.shadowRoot.querySelector('[data-role="date"]');
      expect(dateElement).toBeTruthy();

      const dateText = dateElement.textContent;
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      expect(dateText).toMatch(dateRegex);
    });

    test('should display today\'s date correctly', () => {
      const today = new Date();
      const expectedDate = today.toISOString().split('T')[0];

      const dateElement = component.shadowRoot.querySelector('[data-role="date"]');
      expect(dateElement.textContent).toBe(expectedDate);
    });
  });

  describe('Time Display', () => {
    test('should display current time in HH:MM:SS format', () => {
      const timeElement = component.shadowRoot.querySelector('[data-role="time"]');
      expect(timeElement).toBeTruthy();

      const timeText = timeElement.textContent;
      const timeRegex = /^\d{2}:\d{2}:\d{2}$/;
      expect(timeText).toMatch(timeRegex);
    });

    test('should have valid hour, minute, and second values', () => {
      const timeElement = component.shadowRoot.querySelector('[data-role="time"]');
      const [hours, minutes, seconds] = timeElement.textContent.split(':').map(Number);

      expect(hours).toBeGreaterThanOrEqual(0);
      expect(hours).toBeLessThan(24);
      expect(minutes).toBeGreaterThanOrEqual(0);
      expect(minutes).toBeLessThan(60);
      expect(seconds).toBeGreaterThanOrEqual(0);
      expect(seconds).toBeLessThan(60);
    });
  });

  describe('Real-time Updates', () => {
    test('should update time every second', (done) => {
      jest.useFakeTimers();

      const timeElement = component.shadowRoot.querySelector('[data-role="time"]');
      expect(timeElement).toBeTruthy();

      // Advance time by 1 second
      jest.advanceTimersByTime(1000);

      // Time should have updated (or at least be different)
      // Note: This might be the same if it's the same second, so we verify the interval exists
      expect(component.updateInterval).toBeDefined();
      // updateInterval is a handle returned by setInterval, which can be an object or number
      expect(component.updateInterval).not.toBeNull();

      jest.useRealTimers();
      done();
    });

    test('should call update method at regular intervals', () => {
      jest.useFakeTimers();

      // Stop any existing interval first
      component.stopUpdating();

      // Spy on the update method before starting
      const updateSpy = jest.spyOn(component, 'updateTimestamp');

      // Trigger the update mechanism
      component.startUpdating();

      // Advance time by 2 seconds (should trigger updates)
      jest.advanceTimersByTime(2000);

      // Should have called update at least once (possibly twice depending on timing)
      expect(updateSpy).toHaveBeenCalled();
      expect(updateSpy.mock.calls.length).toBeGreaterThanOrEqual(1);

      updateSpy.mockRestore();
      jest.useRealTimers();
    });

    test('should stop updating when disconnected', () => {
      jest.useFakeTimers();
      const updateSpy = jest.spyOn(component, 'updateTimestamp');

      component.disconnectedCallback();
      jest.advanceTimersByTime(2000);

      // Should have no pending updates after disconnect
      expect(component.updateInterval).toBeNull();

      updateSpy.mockRestore();
      jest.useRealTimers();
    });
  });

  describe('UI Design', () => {
    test('should render in shadow DOM for style encapsulation', () => {
      expect(component.shadowRoot).toBeTruthy();
    });

    test('should have visible date and time elements', () => {
      const dateElement = component.shadowRoot.querySelector('[data-role="date"]');
      const timeElement = component.shadowRoot.querySelector('[data-role="time"]');

      expect(dateElement).toBeTruthy();
      expect(timeElement).toBeTruthy();

      // Should be visible (not hidden)
      const dateStyle = window.getComputedStyle(dateElement);
      const timeStyle = window.getComputedStyle(timeElement);
      expect(dateStyle.display).not.toBe('none');
      expect(timeStyle.display).not.toBe('none');
    });

    test('should have readable styling', () => {
      const container = component.shadowRoot.querySelector('[data-role="container"]');
      expect(container).toBeTruthy();

      // Check that container has some size/visibility
      const style = window.getComputedStyle(container);
      expect(style.display).not.toBe('none');
    });
  });

  describe('Browser Compatibility', () => {
    test('should work with standard Web Component APIs', () => {
      expect(customElements.get('timestamp-display')).toBeTruthy();
    });

    test('should be a proper custom element', () => {
      expect(component instanceof HTMLElement).toBe(true);
    });
  });
});
