# ResearchAI - Development Memory & Critical Configurations

**Version**: 2.1.0  
**Last Updated**: December 25, 2024  
**Purpose**: Prevent recurring issues, document critical configurations

---

## 🚨 CRITICAL RULES - NEVER VIOLATE

### Rule 1: Agent Boundary Enforcement
```
EACH AGENT MAY ONLY OPERATE WITHIN ITS DEFINED RESPONSIBILITY

Violations that MUST be avoided:
- QualityAssuranceAgent rewriting content (it may only FLAG)
- Any agent modifying formatting (only StructureFormattingAgent may)
- Agents bypassing the DAG execution order
- UIUXAgent being disabled or bypassed
```

### Rule 2: Single-Pass Execution
```
THE SYSTEM MUST COMPLETE IN ONE STABLE EXECUTION PASS

Never implement:
- Recursive debugging loops
- Speculative refactoring
- Infinite correction cycles
- Multiple regeneration attempts
```

### Rule 3: Immutable Architecture
```
DO NOT MODIFY:
- Agent execution order
- File/folder names
- Module structure
- Existing working code

All changes must be ADDITIVE and REVERSIBLE
```

---

## 🔐 Google OAuth Configuration

### Backend (.env)
```env
GOOGLE_CLIENT_ID=64290232708-04ab1c328jbkrta9770u6q32olbkqt5p.apps.googleusercontent.com
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_GOOGLE_CLIENT_ID=64290232708-04ab1c328jbkrta9770u6q32olbkqt5p.apps.googleusercontent.com
```

### Backend Endpoint Implementation
```python
# Location: src/api/main.py

@app.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest):
    """
    Accepts Google credential JWT, decodes it, creates/updates user.
    Returns: { access_token, user }
    """
    import base64
    parts = request.credential.split('.')
    payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
    user_info = json.loads(base64.urlsafe_b64decode(payload))
    # Create user and return token
```

### Frontend Implementation
```tsx
// Location: frontend/src/pages/login.tsx

// 1. Load Google Script
<Script 
  src="https://accounts.google.com/gsi/client" 
  onLoad={() => setGoogleReady(true)} 
/>

// 2. Initialize when ready
useEffect(() => {
  if (googleReady && window.google && GOOGLE_CLIENT_ID) {
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleCallback,
    });
    window.google.accounts.id.renderButton(
      document.getElementById('google-btn'),
      { theme: 'filled_black', size: 'large' }
    );
  }
}, [googleReady]);

// 3. Handle callback
const handleGoogleCallback = async (response) => {
  const res = await fetch(`${API_URL}/api/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential: response.credential })
  });
  // Store token and redirect
};
```

### Common Google OAuth Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Button not appearing | Script not loaded | Check `googleReady` state |
| Invalid client ID | Mismatch between frontend/backend | Verify both .env files |
| Callback not firing | Origin not authorized | Add to Google Console |
| Token decode error | Malformed JWT | Check credential format |

---

## 💾 State Management

### Recommended Pattern (Simple, Reliable)
```tsx
// Use localStorage + useState, NOT complex state libraries

// On Login
localStorage.setItem('auth_token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));

// On Mount
useEffect(() => {
  const token = localStorage.getItem('auth_token');
  const userData = localStorage.getItem('user');
  if (token && userData) {
    setUser(JSON.parse(userData));
  }
}, []);

// On Logout
localStorage.removeItem('auth_token');
localStorage.removeItem('user');
```

### Why NOT Zustand/Redux for Auth
```
Previous issues encountered:
- Hydration errors in Next.js
- State not persisting across refreshes
- Complex debugging for simple auth flow

Keep it simple: localStorage + useState
```

---

## 🎨 CSS Strategy

### Use CSS-in-JS with `<style jsx>`
```tsx
// GOOD: Isolated, reliable styles
<div className="component">
  <style jsx>{`
    .component { color: white; }
  `}</style>
</div>

// AVOID: Tailwind class conflicts in complex components
// Tailwind is fine for simple layouts, but JSX styles for complex UIs
```

### Why This Approach
```
1. No class name conflicts
2. Styles always load with component
3. No external CSS file dependencies
4. Easy to debug and modify
```

---

## 📡 API Communication

### Polling Pattern (Recommended)
```tsx
const startPolling = useCallback((jobId: string) => {
  if (pollRef.current) clearInterval(pollRef.current);
  
  const poll = async () => {
    try {
      const res = await fetch(`${API_URL}/api/proposals/jobs/${jobId}`);
      const data = await res.json();
      setJobStatus(data);
      
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch (err) {
      console.error('Poll error:', err);
    }
  };
  
  poll();
  pollRef.current = setInterval(poll, 3000);
}, []);

// IMPORTANT: Cleanup on unmount
useEffect(() => {
  return () => {
    if (pollRef.current) clearInterval(pollRef.current);
  };
}, []);
```

### Why Native Fetch Over Axios
```
For polling operations:
- Native fetch is more reliable
- Fewer dependencies
- Better control over timeouts
- No interceptor conflicts
```

---

## 📋 Subscription Tier Logic

### Tier Definitions
```typescript
type SubscriptionTier = 'free' | 'non_permanent' | 'permanent';

const TIER_FEATURES = {
  free: {
    preview: 300,        // words
    pdfExport: false,
    watermark: 'Preview Version – Upgrade Required'
  },
  non_permanent: {
    preview: Infinity,   // full
    pdfExport: true,
    watermark: 'FOMA Digital Solution'
  },
  permanent: {
    preview: Infinity,   // full
    pdfExport: true,
    watermark: null      // clean
  }
};
```

### Enforcement Points
```
1. Preview API: Limits content for free tier
2. Export API: Blocks PDF for free tier
3. PDF Generation: Adds watermark for non-permanent
4. Frontend UI: Shows upgrade prompts
```

### CRITICAL: Subscription Logic Location
```
Subscription logic exists ONLY at the delivery/export layer.
NO AGENT may be aware of subscription tier.
Agents produce full content regardless of tier.
```

---

## 🖨️ PDF Watermark Implementation

```python
# Location: src/api/main.py

def add_watermark(canvas_obj, doc):
    if subscription_tier == SubscriptionTier.NON_PERMANENT.value:
        canvas_obj.saveState()
        canvas_obj.setFillColor(Color(0.8, 0.8, 0.8, alpha=0.3))
        canvas_obj.setFont('Helvetica-Bold', 50)
        canvas_obj.translate(A4[0]/2, A4[1]/2)
        canvas_obj.rotate(45)
        canvas_obj.drawCentredString(0, 0, "FOMA Digital Solution")
        canvas_obj.restoreState()
```

---

## 🚀 Startup Commands

### Backend
```powershell
cd C:\Users\ashar\Documents\rpa_claude_desktop
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend
```powershell
cd C:\Users\ashar\Documents\rpa_claude_desktop\frontend
npm run dev
```

### Clear Frontend Cache (if issues)
```powershell
cd C:\Users\ashar\Documents\rpa_claude_desktop\frontend
Remove-Item -Recurse -Force .next
npm run dev
```

---

## 🐛 Common Issues & Solutions

### Issue: "missing required error components, refreshing..."
**Cause**: Next.js compilation error  
**Solution**:
1. Delete `.next` folder
2. Check for syntax errors in pages
3. Verify all imports resolve
4. Restart dev server

### Issue: Google OAuth button not appearing
**Cause**: Script not loaded or client ID missing  
**Solution**:
1. Check `NEXT_PUBLIC_GOOGLE_CLIENT_ID` in `.env.local`
2. Verify Script component is present
3. Check `googleReady` state before render

### Issue: Polling stops unexpectedly
**Cause**: Component unmount or error  
**Solution**:
1. Use `useRef` for interval storage
2. Implement proper cleanup
3. Add error handling in poll function

### Issue: PDF export fails
**Cause**: ReportLab error or missing dependency  
**Solution**:
1. Verify reportlab is installed: `pip install reportlab`
2. Check subscription tier is valid
3. Verify proposal data is complete

### Issue: Progress stuck at 0%
**Cause**: Backend job not starting  
**Solution**:
1. Check backend logs for errors
2. Verify ANTHROPIC_API_KEY is set
3. Check job queue is processing

---

## 📊 Performance Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Generation Time | <10 min | Backend logs |
| API Response | <200ms | Network tab |
| PDF Export | <5 sec | Console timing |
| Frontend Load | <2 sec | Lighthouse |

---

## 📁 Key File Locations

| File | Purpose | Do Not Modify |
|------|---------|---------------|
| `src/api/main.py` | Backend API | Structure only |
| `frontend/src/pages/login.tsx` | Auth page | OAuth flow |
| `frontend/src/pages/dashboard.tsx` | Main app | State management |
| `.env` | Backend secrets | Never commit |
| `frontend/.env.local` | Frontend config | Never commit |

---

## ✅ Pre-Deployment Checklist

- [ ] All 13 agents operational
- [ ] Google OAuth working
- [ ] Subscription tiers enforced
- [ ] PDF watermark functional
- [ ] Preview limits working
- [ ] All exports functional
- [ ] Performance targets met
- [ ] Security audit passed

---

## 👨‍💻 Author
**Neural** - PhD Candidate at KFUPM  
Technical Head at FOMA Digital Solution

---

*Memory Document Version: 2.1.0*  
*Last Updated: December 25, 2024*  
*Review Frequency: Every major update*
