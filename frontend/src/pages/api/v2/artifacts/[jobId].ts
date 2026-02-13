import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { jobId } = req.query;

  res.status(200).json({
    proposal_id: jobId,
    topic: 'Research Proposal',
    version: '2.5.0',
    artifacts: {
      version: '2.5.0',
      artifact_count: 2,
      artifacts: [
        {
          type: 'gantt_chart',
          title: 'Project Timeline',
          format: 'mermaid',
          mermaid_code: 'gantt\n    title Research Timeline\n    dateFormat YYYY-MM-DD\n    section Phase 1\n    Literature Review :a1, 2024-01-01, 90d\n    section Phase 2\n    Data Collection :a2, after a1, 120d',
          placement: 'appendix'
        },
        {
          type: 'work_breakdown_structure',
          title: 'Work Breakdown Structure',
          format: 'mermaid',
          mermaid_code: 'graph TD\n    A[Research Project] --> B[Phase 1: Planning]\n    A --> C[Phase 2: Execution]\n    A --> D[Phase 3: Analysis]',
          placement: 'methodology'
        }
      ]
    }
  });
}
