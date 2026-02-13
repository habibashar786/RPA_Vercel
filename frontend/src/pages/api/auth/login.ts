import type { NextApiRequest, NextApiResponse } from 'next';
import { usersStore, generateToken } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ detail: 'Method not allowed' });
  }

  const { email, password } = req.body;
  const user = usersStore[email];

  if (!user || user.password !== password) {
    return res.status(401).json({ detail: 'Invalid credentials' });
  }

  if (user.authProvider === 'google') {
    return res.status(400).json({ detail: 'Please use Google Sign-In' });
  }

  const token = generateToken(user.id);

  res.status(200).json({
    access_token: token,
    token_type: 'bearer',
    user: {
      id: user.id,
      email: user.email,
      name: user.name,
      picture: user.picture,
      subscription_tier: user.subscriptionTier
    }
  });
}
