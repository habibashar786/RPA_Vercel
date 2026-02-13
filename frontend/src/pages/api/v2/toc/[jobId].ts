import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { jobId } = req.query;
  
  res.status(200).json({
    version: '2.5.0',
    title: 'Table of Contents',
    entry_count: 8,
    entries: [
      { title: 'Abstract', level: 'chapter', page: 'i', number: '', indent: 0 },
      { title: 'Introduction', level: 'chapter', page: '1', number: '1', indent: 0 },
      { title: 'Literature Review', level: 'chapter', page: '5', number: '2', indent: 0 },
      { title: 'Methodology', level: 'chapter', page: '15', number: '3', indent: 0 },
      { title: 'Expected Results', level: 'chapter', page: '25', number: '4', indent: 0 },
      { title: 'Timeline & Budget', level: 'chapter', page: '30', number: '5', indent: 0 },
      { title: 'Conclusion', level: 'chapter', page: '35', number: '6', indent: 0 },
      { title: 'References', level: 'chapter', page: '38', number: '', indent: 0 }
    ]
  });
}
