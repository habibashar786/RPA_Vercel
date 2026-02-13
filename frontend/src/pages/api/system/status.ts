import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({
    status: 'operational',
    agents_count: 12,
    version: '2.5.0',
    environment: 'vercel-nextjs'
  });
}
