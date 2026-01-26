# Timestamp Display Component

A reusable Web Component that displays the current date and time with real-time updates.

## Features

- ✅ Displays current date in `YYYY-MM-DD` format
- ✅ Displays current time in `HH:MM:SS` format
- ✅ Updates every second automatically
- ✅ Clean, glass-morphism UI design
- ✅ Works in all modern browsers
- ✅ Shadow DOM encapsulation for style isolation
- ✅ Fully tested with Jest

## Usage

### Basic Usage

```html
<!DOCTYPE html>
<html>
<head>
  <script src="src/timestamp-display.js"></script>
</head>
<body>
  <timestamp-display></timestamp-display>
</body>
</html>
```

### Installation

1. Include the component script in your HTML:
```html
<script src="path/to/timestamp-display.js"></script>
```

2. Use the component:
```html
<timestamp-display></timestamp-display>
```

## Component API

### Custom Element Tag
`<timestamp-display></timestamp-display>`

### Properties
- `updateInterval`: The interval ID for the update loop (number or object)

### Methods
- `updateTimestamp()`: Updates the displayed time immediately
- `startUpdating()`: Starts the automatic update loop
- `stopUpdating()`: Stops the automatic update loop

### Lifecycle
- **connectedCallback**: Automatically starts updating when added to DOM
- **disconnectedCallback**: Automatically stops updating when removed from DOM

## Styling

The component uses Shadow DOM for style encapsulation. The default styling includes:

- Glass morphism design with backdrop blur
- Responsive layout
- Monospace font for time display
- Centered content with padding

### Custom Styling

To customize the component's appearance, you can use CSS custom properties in a future version, or modify the styles in `src/timestamp-display.js`.

## Testing

Run the test suite:

```bash
npm test
```

The component includes 12 comprehensive tests covering:
- Date display accuracy and format
- Time display accuracy and format
- Real-time updates every second
- Shadow DOM encapsulation
- Browser compatibility
- Lifecycle management

## Example

See `example.html` for a complete working example with a purple gradient background.

## Browser Support

The component uses modern Web APIs:
- Custom Elements (Web Components)
- Shadow DOM
- Template literals
- Arrow functions

Supported browsers:
- Chrome/Edge 67+
- Firefox 63+
- Safari 13+
- Opera 54+

## Acceptance Criteria - Status

- ✅ Display current date in format YYYY-MM-DD
- ✅ Display current time in format HH:MM:SS
- ✅ Time updates every second automatically
- ✅ Clean, readable UI design
- ✅ Works in all modern browsers
