// Shared storage and utilities for API routes

// In-memory storage (resets on cold start - use database for production)
export const usersStore: Record<string, any> = {
  "demo@researchai.com": {
    id: "demo-user-001",
    email: "demo@researchai.com",
    name: "Demo User",
    password: "demo123",
    picture: null,
    subscriptionTier: "permanent",
    authProvider: "email"
  }
};

export const tokensStore: Record<string, string> = {};
export const jobsStore: Record<string, any> = {};
export const proposalsStore: Record<string, any> = {};

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

export function generateToken(userId: string): string {
  const token = `tk_${generateId()}`;
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
