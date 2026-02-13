import type { NextApiRequest, NextApiResponse } from 'next';
import { proposalsStore } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { jobId } = req.query;
  const id = Array.isArray(jobId) ? jobId[0] : jobId;

  const proposal = proposalsStore[id as string];
  if (!proposal) {
    return res.status(404).json({ detail: 'Proposal not found' });
  }

  res.status(200).json(proposal);
}
