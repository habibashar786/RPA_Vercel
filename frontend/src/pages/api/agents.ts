import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({
    agents: [
      { name: 'Central Orchestrator', status: 'active' },
      { name: 'Introduction Agent', status: 'active' },
      { name: 'Literature Review Agent', status: 'active' },
      { name: 'Methodology Agent', status: 'active' },
      { name: 'Structure Agent', status: 'active' },
      { name: 'Citation Agent', status: 'active' },
      { name: 'QA Agent', status: 'active' },
      { name: 'Final Assembly Agent', status: 'active' },
      { name: 'Scopus Compliance Agent', status: 'active' },
      { name: 'Reviewer Simulation Agent', status: 'active' },
      { name: 'Visualization Agent', status: 'active' },
      { name: 'Humanizer Agent', status: 'active' }
    ],
    total: 12
  });
}
