/**
 * TimestampDisplay Web Component
 * Displays current date and time with real-time updates
 */

class TimestampDisplay extends HTMLElement {
  constructor() {
    super();
    this.updateInterval = null;
    this.attachShadow({ mode: 'open' });
    this.render();
    this.dateElement = this.shadowRoot.querySelector('[data-role="date"]');
    this.timeElement = this.shadowRoot.querySelector('[data-role="time"]');
  }

  connectedCallback() {
    this.startUpdating();
  }

  disconnectedCallback() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  render() {
    const styles = `
      :host {
        display: block;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      }

      [data-role="container"] {
        padding: 24px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        max-width: 400px;
        margin: 0 auto;
      }

      [data-role="label"] {
        display: block;
        font-size: 14px;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 8px;
        font-weight: 500;
        letter-spacing: 0.5px;
      }

      [data-role="date"],
      [data-role="time"] {
        display: block;
        font-size: 48px;
        font-weight: 300;
        color: #ffffff;
        text-align: center;
        letter-spacing: 2px;
        font-family: 'Courier New', monospace;
        line-height: 1.2;
      }

      [data-role="date"] {
        font-size: 36px;
        margin-bottom: 16px;
        color: rgba(255, 255, 255, 0.95);
      }

      [data-role="time"] {
        font-size: 56px;
        font-weight: 300;
        color: #ffffff;
      }

      [data-role="divider"] {
        height: 1px;
        background: rgba(255, 255, 255, 0.2);
        margin: 16px 0;
      }

      [data-role="info"] {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        text-align: center;
        margin-top: 12px;
      }
    `;

    const now = new Date();
    const dateStr = this.formatDate(now);
    const timeStr = this.formatTime(now);

    this.shadowRoot.innerHTML = `
      <style>${styles}</style>
      <div data-role="container">
        <div data-role="label">Current Date & Time</div>
        <div data-role="date">${dateStr}</div>
        <div data-role="divider"></div>
        <div data-role="time">${timeStr}</div>
        <div data-role="info">Live updating every second</div>
      </div>
    `;
  }

  formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  formatTime(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  }

  updateTimestamp() {
    const now = new Date();
    const dateStr = this.formatDate(now);
    const timeStr = this.formatTime(now);

    if (this.dateElement) {
      this.dateElement.textContent = dateStr;
    }
    if (this.timeElement) {
      this.timeElement.textContent = timeStr;
    }
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
}

// Register the custom element
customElements.define('timestamp-display', TimestampDisplay);

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TimestampDisplay;
}
