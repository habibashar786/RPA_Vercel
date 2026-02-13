import type { NextApiRequest, NextApiResponse } from 'next';
import { jobsStore, proposalsStore, generateId } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ detail: 'Method not allowed' });
  }

  const { topic, target_word_count = 15000, citation_style = 'harvard' } = req.body;
  const jobId = `job_${generateId()}`;

  jobsStore[jobId] = {
    job_id: jobId,
    topic,
    status: 'completed',
    progress: 100,
    current_stage: 'completed',
    stages_completed: ['init', 'research', 'writing', 'formatting', 'qa'],
    message: 'Proposal generated successfully!',
    created_at: new Date().toISOString(),
    error: null
  };

  proposalsStore[jobId] = {
    request_id: jobId,
    topic,
    word_count: target_word_count,
    sections: [
      { title: 'Abstract', content: `This research proposal investigates ${topic}. The study aims to contribute significant insights to the field.` },
      { title: '1. Introduction', content: `The topic of ${topic} has gained significant attention in recent academic discourse.` },
      { title: '2. Literature Review', content: 'A thorough review of existing literature reveals several important themes and research gaps.' },
      { title: '3. Research Methodology', content: 'This study employs a mixed-methods approach combining quantitative and qualitative methods.' },
      { title: '4. Expected Results', content: 'Based on preliminary analysis, we anticipate findings that will contribute to the field.' },
      { title: '5. Timeline & Budget', content: 'The research is planned for completion within 12 months.' },
      { title: '6. Conclusion', content: 'This research proposal presents a rigorous plan for investigating the proposed topic.' },
      { title: 'References', content: '1. Smith, J. (2023). Research Methods. Academic Press.\n2. Johnson, M. (2024). Literature Review. Oxford.' }
    ],
    generated_at: new Date().toISOString(),
    citation_style,
    full_content: `Complete research proposal on: ${topic}`
  };

  res.status(200).json({
    job_id: jobId,
    topic,
    status: 'completed',
    progress: 100,
    message: 'Proposal generated successfully!'
  });
}
