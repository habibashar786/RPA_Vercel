# ResearchAI - Vercel Full-Stack Deployment

AI-Powered Multi-Agent Research Proposal Generator - Full-stack deployment on Vercel.

## Architecture

```
rpa_vercel/
├── api/                    # Python Serverless API
│   ├── index.py           # FastAPI serverless handler
│   └── requirements.txt   # Python dependencies
├── frontend/              # Next.js Frontend
│   ├── src/
│   │   ├── pages/        # React pages
│   │   ├── services/     # API client
│   │   └── styles/       # CSS
│   └── package.json
└── vercel.json            # Vercel configuration
```

## Features

- 🤖 **12 AI Agents** - Multi-agent orchestration
- 📊 **Scopus Q1 Compliance** - Quality assessment
- 👥 **Peer Review Simulation** - Academic feedback
- 📈 **Project Artifacts** - Gantt charts, WBS, RTM
- 📑 **Export Formats** - PDF, DOCX, Markdown

## Deployment

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/habibashar786/rpa-vercel)

### Manual Deployment

1. Push to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/rpa-vercel.git
git push -u origin main
```

2. Connect to Vercel:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your repository
   - Deploy!

## Demo Credentials

- **Email:** demo@researchai.com
- **Password:** demo123

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/auth/login` | POST | User login |
| `/api/auth/signup` | POST | User registration |
| `/api/proposals/generate` | POST | Generate proposal |
| `/api/proposals/jobs/{id}` | GET | Job status |
| `/api/v2/scopus/compliance/{id}` | GET | Scopus analysis |
| `/api/v2/review/simulate/{id}` | GET | Peer review |

## Tech Stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS
- **Backend:** FastAPI (Python Serverless)
- **Deployment:** Vercel

## License

MIT License
