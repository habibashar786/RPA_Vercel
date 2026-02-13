import type { NextApiRequest, NextApiResponse } from 'next';
import { jobsStore, proposalsStore } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { jobId } = req.query;
  const id = Array.isArray(jobId) ? jobId[0] : jobId;

  // Check if requesting result
  if (req.url?.includes('/result')) {
    const proposal = proposalsStore[id as string];
    if (!proposal) {
      return res.status(404).json({ detail: 'Proposal not found' });
    }
    return res.status(200).json(proposal);
  }

  const job = jobsStore[id as string];
  if (!job) {
    return res.status(404).json({ detail: 'Job not found' });
  }

  res.status(200).json(job);
}
