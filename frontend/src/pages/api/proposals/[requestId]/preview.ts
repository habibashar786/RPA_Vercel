import type { NextApiRequest, NextApiResponse } from 'next';
import { proposalsStore } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { requestId } = req.query;
  const id = Array.isArray(requestId) ? requestId[0] : requestId;

  const proposal = proposalsStore[id as string];
  if (!proposal) {
    return res.status(404).json({ detail: 'Proposal not found' });
  }

  const html = `
    <html>
    <head><style>
      body { font-family: 'Times New Roman', serif; max-width: 800px; margin: 0 auto; padding: 20px; }
      h1 { color: #1a365d; text-align: center; }
      h2 { color: #2d3748; border-bottom: 2px solid #4a5568; padding-bottom: 5px; }
      p { line-height: 1.8; text-align: justify; }
    </style></head>
    <body>
      <h1>${proposal.topic}</h1>
      <p><strong>Word Count:</strong> ${proposal.word_count}</p>
      <hr>
      ${proposal.sections.map((s: any) => `<h2>${s.title}</h2><p>${s.content}</p>`).join('')}
    </body>
    </html>
  `;

  res.status(200).json({ html, word_count: proposal.word_count });
}
