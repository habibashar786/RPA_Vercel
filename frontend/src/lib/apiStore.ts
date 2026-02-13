// Shared storage and utilities for API routes
import { v4 as uuidv4 } from 'uuid';

// In-memory storage (resets on cold start, but persists across requests)
export const usersStore: Record<string, any> = {
  "demo@researchai.com": {
    id: "demo-user-001",
    email: "demo@researchai.com",
    name: "Demo User",
    password: "demo123",
    picture: null,
    subscription_tier: "permanent",
    auth_provider: "email"
  }
};

export const tokensStore: Record<string, string> = {};
export const jobsStore: Record<string, any> = {};
export const proposalsStore: Record<string, any> = {};

export function generateToken(userId: string): string {
  const token = `tk_${uuidv4().replace(/-/g, '').slice(0, 32)}`;
  tokensStore[token] = userId;
  return token;
}

export function getUserFromToken(authHeader: string | undefined): any | null {
  if (!authHeader) return null;
  const token = authHeader.replace('Bearer ', '');
  const userId = tokensStore[token];
  if (!userId) return null;
  
  for (const user of Object.values(usersStore)) {
    if (user.id === userId) return user;
  }
  return null;
}

export function decodeGoogleJwt(token: string): any | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    
    let payload = parts[1];
    // Add padding if needed
    const padding = 4 - (payload.length % 4);
    if (padding !== 4) {
      payload += '='.repeat(padding);
    }
    
    const decoded = Buffer.from(payload, 'base64').toString('utf-8');
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

export function generateUuid(): string {
  return uuidv4().replace(/-/g, '').slice(0, 12);
}
