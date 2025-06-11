# Smart Segments Frontend

This is the frontend application for Smart Segments, built with Next.js and Material-UI.

## Features

- Server-side rendering for better SEO
- Material Design UI components
- File upload and analysis
- Interactive data visualization
- Responsive design

## Getting Started

### Prerequisites

- Node.js 18.x or later
- npm 9.x or later

### Installation

1. Clone the repository
2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file in the root directory with the following content:
```
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_SHOW_CATEGORY_ANALYSIS=false
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Building for Production

```bash
npm run build
```

The build output will be in the `out` directory.

### Deployment

The application can be deployed to any static hosting service that supports Next.js static exports, such as:

- Vercel
- Netlify
- GitHub Pages
- Zeabur

## SEO Optimization

The application includes:

- Server-side rendering
- Meta tags for social sharing
- Schema.org structured data
- Sitemap.xml
- Robots.txt

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_SHOW_CATEGORY_ANALYSIS`: Enable/disable category analysis feature

## License

MIT