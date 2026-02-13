import type { NextApiRequest, NextApiResponse } from 'next';
import { jobsStore } from '../../../lib/apiStore';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({
    jobs: Object.values(jobsStore),
    total: Object.keys(jobsStore).length
  });
}
