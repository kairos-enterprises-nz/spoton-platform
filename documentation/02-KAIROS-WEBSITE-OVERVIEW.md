# Kairos Enterprises - Single Page Application

A modern, self-hosted single-page React website for Kairos Enterprises featuring an animated Orb background and responsive design.

## Features

- **Modern React SPA**: Built with React 18 and Tailwind CSS
- **Animated Background**: Uses reactbits Orb component for dynamic visual effects
- **Responsive Design**: Optimized for desktop and mobile devices
- **Contact Modal**: Clean modal interface for contact information
- **Self-Hosted**: Containerized with Docker and served via Caddy
- **Accessibility**: Keyboard navigation and ARIA labels included

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ (for local development)

### Production Deployment

1. **Clone and build the application:**
   ```bash
   docker-compose up -d
   ```

   This will:
   - Build the React application
   - Create a production-optimized Docker image
   - Serve the application on port 80

2. **Access the website:**
   Open your browser and navigate to `http://localhost:3005` (or your server's IP address:3005)

### Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000`

## Project Structure

```
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/
│   │   ├── OrbBackground.js    # Animated Orb background
│   │   ├── LogoCenter.js       # Centered logo with contact button
│   │   └── ContactModal.js     # Contact information modal
│   ├── assets/
│   │   └── kairosenterprises-logo.png
│   ├── App.js              # Main application component
│   ├── index.js            # React entry point
│   └── index.css           # Global styles with Tailwind
├── Dockerfile              # Multi-stage Docker build
├── Caddyfile              # Caddy web server configuration
├── docker-compose.yml     # Docker Compose configuration
├── tailwind.config.js     # Tailwind CSS configuration
└── package.json           # Node.js dependencies and scripts
```

## Configuration

### Environment Variables

The application can be customized using environment variables during the Docker build process:

- `REACT_APP_CONTACT_EMAIL`: Contact email (default: contact@kairosenterprises.com)
- `REACT_APP_CONTACT_PHONE`: Contact phone (default: +64 3 123 4567)

Example:
```bash
docker build --build-arg REACT_APP_CONTACT_EMAIL=info@example.com .
```

### Caddy Configuration

The `Caddyfile` is configured to:
- Serve static files with gzip compression
- Handle SPA routing (all routes serve index.html)
- Log requests to stdout
- Listen on port 80

### Customization

#### Logo
Replace `src/assets/kairosenterprises-logo.png` with your own logo.

#### Contact Information
Update the contact details in `src/components/ContactModal.js`.

#### Styling
Modify `tailwind.config.js` to customize the theme, or edit component styles directly.

## Docker Commands

### Build and run:
```bash
docker-compose up -d
```

**Note**: The application runs on port 3005 by default. You can change this in `docker-compose.yml` if needed.

### View logs:
```bash
docker-compose logs -f web
```

### Stop the application:
```bash
docker-compose down
```

### Rebuild after changes:
```bash
docker-compose up -d --build
```

## Development Scripts

- `npm start`: Start development server
- `npm run build`: Build for production
- `npm test`: Run tests
- `npm run eject`: Eject from Create React App (not recommended)

## Browser Support

This application supports all modern browsers including:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

The application is optimized for performance with:
- Code splitting and lazy loading
- Optimized images
- Gzip compression
- Minimal bundle size
- Efficient CSS with Tailwind's purging

## Security

- No sensitive data exposed in client-side code
- HTTPS ready (configure Caddy with your domain and certificates)
- Content Security Policy headers can be added to Caddyfile
- Docker container runs with minimal privileges

## License

This project is proprietary to Kairos Enterprises.

## Support

For technical support or questions, contact: contact@kairosenterprises.com 