import type { NextApiRequest, NextApiResponse } from 'next';
import { getUserFromToken } from '../../../lib/apiStore';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const authHeader = req.headers.authorization;
  const user = getUserFromToken(authHeader);

  if (!user) {
    return res.status(401).json({ detail: 'Not authenticated' });
  }

  res.status(200).json({
    id: user.id,
    email: user.email,
    name: user.name,
    picture: user.picture,
    subscription_tier: user.subscription_tier
  });
}
