import type { NextApiRequest, NextApiResponse } from 'next';
import { generateId } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({
    passed: true,
    similarity_score: 12.5,
    ai_detection_score: 8.2,
    source_breakdown: [
      { source: 'Academic journals', percentage: 5.2 },
      { source: 'Web sources', percentage: 4.8 },
      { source: 'Books', percentage: 2.5 }
    ],
    certificate: {
      id: `cert_${generateId().slice(0, 8)}`,
      issued_at: new Date().toISOString(),
      status: 'valid'
    }
  });
}
