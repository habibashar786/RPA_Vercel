# RPA Claude Desktop - Research Proposal Generator

A powerful AI-powered multi-agent system for generating Q1 journal-standard research proposals.

## Features

- 🤖 **18+ AI Agents** working collaboratively to generate comprehensive research proposals
- 📊 **Scopus Q1 Compliance** - Built-in quality assessment for journal standards
- 👥 **Peer Review Simulation** - Multi-persona review system
- 📈 **Project Artifacts** - Gantt charts, WBS, RTM, Kanban boards
- 📑 **Multiple Export Formats** - PDF, DOCX, Markdown
- 🎨 **Modern UI** - Built with Next.js, Tailwind CSS, and Framer Motion

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **State Management**: Zustand
- **UI Components**: Headless UI, Lucide Icons
- **Forms**: React Hook Form + Zod validation
- **Notifications**: React Hot Toast
- **Charts**: Mermaid.js

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rpa-claude-desktop.git
cd rpa-claude-desktop
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env.local
```

4. Update `.env.local` with your API URL:
```
NEXT_PUBLIC_API_URL=your-api-url
```

5. Run development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

## Deployment

This project is configured for Vercel deployment:

```bash
npm run build
vercel deploy
```

### Environment Variables for Vercel

Set these in your Vercel dashboard:
- `NEXT_PUBLIC_API_URL` - Your backend API URL
- `NEXT_PUBLIC_APP_NAME` - App name (default: ResearchAI)
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID` - (Optional) Google OAuth client ID

## Project Structure

```
├── public/
│   └── favicon.svg
├── src/
│   ├── pages/
│   │   ├── _app.tsx
│   │   ├── index.tsx
│   │   ├── dashboard.tsx
│   │   ├── login.tsx
│   │   └── signup.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── store.ts
│   └── styles/
│       └── globals.css
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── vercel.json
```

## License

MIT License

## Author

Built with ❤️ using Claude AI
