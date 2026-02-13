import type { NextApiRequest, NextApiResponse } from 'next';
import { usersStore, generateToken, generateId, decodeGoogleJwt } from '@/lib/store';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ detail: 'Method not allowed' });
  }

  const { credential } = req.body;
  const googleData = decodeGoogleJwt(credential);

  if (!googleData) {
    return res.status(400).json({ detail: 'Invalid Google credential' });
  }

  const email = googleData.email;
  const name = googleData.name || 'Google User';
  const picture = googleData.picture;

  if (!email) {
    return res.status(400).json({ detail: 'Email not provided by Google' });
  }

  let user = usersStore[email];

  if (user) {
    // Update existing user
    user.name = name;
    user.picture = picture;
  } else {
    // Create new user
    const userId = `google_${generateId()}`;
    user = {
      id: userId,
      email,
      name,
      picture,
      subscriptionTier: 'free',
      authProvider: 'google'
    };
    usersStore[email] = user;
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
