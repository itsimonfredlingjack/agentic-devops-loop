/**
 * Test setup for DOM testing in Node environment
 * Provides mocks for Web Components and DOM APIs
 */

// Mock EventTarget
global.EventTarget = class EventTarget {
  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() {}
};

// Note: shadowDOMElements can be used for future enhancements

// Mock Shadow DOM Root
class MockShadowRoot {
  constructor(host) {
    this.host = host;
    this.mode = 'open';
    this.innerHTML = '';
    this.elements = {};
  }

  querySelector(selector) {
    // Parse data-role selector
    const roleMatch = selector.match(/\[data-role="([^"]+)"\]/);
    if (roleMatch) {
      const role = roleMatch[1];
      if (!this.elements[role]) {
        this.elements[role] = {
          textContent: this.getDefaultContent(role),
          getAttribute: jest.fn(),
          setAttribute: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn()
        };
      }
      return this.elements[role];
    }
    return null;
  }

  querySelectorAll(selector) {
    const result = this.querySelector(selector);
    return result ? [result] : [];
  }

  getDefaultContent(role) {
    const now = new Date();
    if (role === 'date') {
      return now.toISOString().split('T')[0];
    }
    if (role === 'time') {
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const seconds = String(now.getSeconds()).padStart(2, '0');
      return `${hours}:${minutes}:${seconds}`;
    }
    return '';
  }
}

// Mock HTMLElement
const MockHTMLElement = class extends EventTarget {
  constructor() {
    super();
    this._shadowRoot = null;
    this.updateInterval = null;
    this.tagName = 'TIMESTAMP-DISPLAY';
    this.attributes = {};
  }

  attachShadow(options) {
    if (!this._shadowRoot) {
      this._shadowRoot = new MockShadowRoot(this);
      this._shadowRoot.mode = options.mode || 'open';
    }
    return this._shadowRoot;
  }

  get shadowRoot() {
    return this._shadowRoot;
  }

  updateTimestamp() {
    // Implemented by component
  }

  startUpdating() {
    if (this.updateInterval === null) {
      this.updateInterval = setInterval(() => this.updateTimestamp(), 1000);
    }
  }

  stopUpdating() {
    if (this.updateInterval !== null) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  connectedCallback() {
    if (typeof super.connectedCallback === 'function') {
      super.connectedCallback();
    }
  }

  disconnectedCallback() {
    this.stopUpdating();
  }

  getAttribute(name) {
    return this.attributes[name] || null;
  }

  setAttribute(name, value) {
    this.attributes[name] = value;
  }
};

global.HTMLElement = MockHTMLElement;

// Store registered components
const registeredComponents = {};

// Mock customElements
global.customElements = {
  define: jest.fn((name, componentClass) => {
    registeredComponents[name] = componentClass;
  }),
  get: jest.fn((name) => {
    return registeredComponents[name] || null;
  })
};

// Mock document
global.document = {
  body: {
    innerHTML: ''
  },
  querySelector: jest.fn((selector) => {
    if (selector === 'timestamp-display') {
      const ComponentClass = registeredComponents['timestamp-display'];
      if (ComponentClass) {
        const elem = new ComponentClass();
        elem.connectedCallback();
        return elem;
      }
    }
    return null;
  }),
  querySelectorAll: jest.fn(() => []),
  createElement: jest.fn((tag) => {
    if (tag === 'timestamp-display') {
      const ComponentClass = registeredComponents['timestamp-display'];
      if (ComponentClass) {
        return new ComponentClass();
      }
    }
    return new MockHTMLElement();
  })
};

// Mock window.getComputedStyle
global.window = {
  getComputedStyle: jest.fn(() => ({
    display: 'block',
    visibility: 'visible'
  }))
};

// Load the component after mocks are in place
require('../src/timestamp-display');
