import type { NextApiRequest, NextApiResponse } from 'next';
import { proposalsStore } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { requestId, format } = req.query;
  const id = Array.isArray(requestId) ? requestId[0] : requestId;
  const fmt = Array.isArray(format) ? format[0] : format;

  const proposal = proposalsStore[id as string];
  if (!proposal) {
    return res.status(404).json({ detail: 'Proposal not found' });
  }

  if (fmt === 'markdown') {
    let content = `# ${proposal.topic}\n\n`;
    for (const section of proposal.sections) {
      content += `## ${section.title}\n\n${section.content}\n\n`;
    }
    return res.status(200).json({ content, filename: `${id}_proposal.md` });
  }

  res.status(200).json({ message: `Export to ${fmt}`, filename: `${id}_proposal.${fmt}` });
}
