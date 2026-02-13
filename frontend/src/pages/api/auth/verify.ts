import type { NextApiRequest, NextApiResponse } from 'next';
import { getUserFromToken } from '../../../lib/apiStore';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const authHeader = req.headers.authorization;
  const user = getUserFromToken(authHeader);
  res.status(200).json({ valid: user !== null });
}
