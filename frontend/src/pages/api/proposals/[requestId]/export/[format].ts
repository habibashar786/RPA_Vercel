import type { NextApiRequest, NextApiResponse } from 'next';
import { proposalsStore } from '../../../../../lib/apiStore';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { requestId, format } = req.query;
  const requestIdStr = Array.isArray(requestId) ? requestId[0] : requestId;
  const formatStr = Array.isArray(format) ? format[0] : format;

  const proposal = proposalsStore[requestIdStr || ''];
  
  if (!proposal) {
    return res.status(404).json({ detail: 'Proposal not found' });
  }

  if (formatStr === 'markdown') {
    let content = `# ${proposal.topic}\n\n`;
    for (const section of proposal.sections) {
      content += `## ${section.title}\n\n${section.content}\n\n`;
    }
    return res.status(200).json({ content, filename: `${requestIdStr}_proposal.md` });
  }

  res.status(200).json({
    message: `Export to ${formatStr} format`,
    filename: `${requestIdStr}_proposal.${formatStr}`
  });
}
