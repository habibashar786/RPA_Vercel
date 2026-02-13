import type { NextApiRequest, NextApiResponse } from 'next';
import { jobsStore } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const jobs = Object.values(jobsStore);
  res.status(200).json({ jobs, total: jobs.length });
}
