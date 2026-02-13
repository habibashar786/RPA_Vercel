import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({
    tiers: [
      {
        id: 'free',
        name: 'Free',
        price: 0,
        features: ['3 proposals/month', 'Basic formatting', 'Markdown export'],
        limitations: ['Watermarked PDFs', 'Limited word count']
      },
      {
        id: 'non_permanent',
        name: 'Standard',
        price: 9.99,
        features: ['10 proposals/month', 'Full formatting', 'PDF export'],
        limitations: ['Watermarked PDFs']
      },
      {
        id: 'permanent',
        name: 'Premium',
        price: 19.99,
        features: ['Unlimited proposals', 'Full formatting', 'Clean PDF export', 'Priority support'],
        limitations: []
      }
    ]
  });
}
