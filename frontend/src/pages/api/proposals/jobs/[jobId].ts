import type { NextApiRequest, NextApiResponse } from 'next';
import { jobsStore, proposalsStore } from '../../../../lib/apiStore';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { jobId } = req.query;
  const jobIdStr = Array.isArray(jobId) ? jobId[0] : jobId;

  if (!jobIdStr) {
    return res.status(400).json({ detail: 'Job ID required' });
  }

  // Check if this is a result request
  const url = req.url || '';
  if (url.includes('/result')) {
    const proposal = proposalsStore[jobIdStr];
    if (!proposal) {
      return res.status(404).json({ detail: 'Proposal not found' });
    }
    return res.status(200).json(proposal);
  }

  // Return job status
  const job = jobsStore[jobIdStr];
  if (!job) {
    return res.status(404).json({ detail: 'Job not found' });
  }

  res.status(200).json(job);
}
