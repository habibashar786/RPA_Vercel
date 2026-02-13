import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { jobId } = req.query;

  res.status(200).json({
    job_id: jobId,
    overall_assessment: 'minor_revision',
    consensus_score: 82.5,
    agreement_level: 'high',
    reviewer_feedback: [
      {
        persona_id: 'rev_1',
        persona_name: 'Dr. Methodology Expert',
        focus_area: 'Research Design',
        score: 0.85,
        recommendation: 'Accept with minor revisions',
        strengths: ['Clear research objectives', 'Appropriate methodology'],
        weaknesses: ['Limited sample size discussion'],
        suggestions: ['Expand validity discussion']
      },
      {
        persona_id: 'rev_2',
        persona_name: 'Prof. Literature Specialist',
        focus_area: 'Literature Review',
        score: 0.82,
        recommendation: 'Accept with minor revisions',
        strengths: ['Comprehensive coverage', 'Good synthesis'],
        weaknesses: ['Missing recent publications'],
        suggestions: ['Include 2024 publications']
      }
    ],
    aggregated_strengths: ['Well-structured', 'Clear objectives', 'Rigorous approach'],
    aggregated_weaknesses: ['Some gaps in recent literature'],
    priority_revisions: ['Update literature review', 'Expand methodology']
  });
}
