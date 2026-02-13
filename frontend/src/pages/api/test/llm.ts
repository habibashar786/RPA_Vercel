import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({
    status: 'operational',
    provider: 'anthropic',
    model: 'claude-3-sonnet',
    response_time_ms: 150
  });
}
