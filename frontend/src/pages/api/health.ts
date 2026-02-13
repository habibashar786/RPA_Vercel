import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({
    status: 'healthy',
    version: '2.5.0',
    timestamp: new Date().toISOString(),
    service: 'ResearchAI API (Next.js)'
  });
}
