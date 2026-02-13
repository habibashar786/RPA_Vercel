import type { NextApiRequest, NextApiResponse } from 'next';
import { usersStore, generateToken, generateId } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ detail: 'Method not allowed' });
  }

  const { email, password, name } = req.body;

  if (usersStore[email]) {
    return res.status(400).json({ detail: 'Email already registered' });
  }

  const userId = `user_${generateId()}`;
  usersStore[email] = {
    id: userId,
    email,
    name,
    password,
    picture: null,
    subscriptionTier: 'free',
    authProvider: 'email'
  };

  const token = generateToken(userId);

  res.status(200).json({
    access_token: token,
    token_type: 'bearer',
    user: {
      id: userId,
      email,
      name,
      picture: null,
      subscription_tier: 'free'
    }
  });
}
