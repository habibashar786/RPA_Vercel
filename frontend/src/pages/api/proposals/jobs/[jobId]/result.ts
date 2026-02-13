import type { NextApiRequest, NextApiResponse } from 'next';
import { proposalsStore } from '../../../../lib/apiStore';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { jobId } = req.query;
  const jobIdStr = Array.isArray(jobId) ? jobId[0] : jobId;

  if (!jobIdStr) {
    return res.status(400).json({ detail: 'Job ID required' });
  }

  const proposal = proposalsStore[jobIdStr];
  if (!proposal) {
    return res.status(404).json({ detail: 'Proposal not found' });
  }

  res.status(200).json(proposal);
}
