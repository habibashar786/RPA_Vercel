import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { jobId } = req.query;

  res.status(200).json({
    job_id: jobId,
    overall_score: 0.87,
    q1_ready: true,
    quality_level: 'High',
    acceptance_probability: {
      estimate: 0.78,
      confidence_interval: [0.72, 0.84],
      confidence_level: 0.95
    },
    criteria_scores: {
      originality: 0.85,
      methodology: 0.88,
      literature_coverage: 0.90,
      clarity: 0.86,
      structure: 0.89
    },
    recommendations: [
      'Consider expanding the methodology section',
      'Add more recent references (2023-2024)',
      'Strengthen the theoretical framework'
    ]
  });
}
