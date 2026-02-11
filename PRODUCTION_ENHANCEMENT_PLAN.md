# ResearchAI Production Enhancement Plan
## Master Prompt Analysis & Implementation Strategy

---

## 📋 EXECUTIVE SUMMARY

This document outlines the precise, minimal, production-critical enhancements for the ResearchAI platform based on the Master Prompt requirements.

---

## 🎯 REQUIREMENTS ANALYSIS

### 1. TITLE PAGE (Image-Aligned)
| Element | Requirement | Implementation |
|---------|-------------|----------------|
| Research Title | Centered, uppercase, upper-middle | PDF generation layer |
| Author Name | Centered, title case, from user profile | Dynamic injection |
| Document Label | "RESEARCH PROPOSAL", centered, uppercase | Static text |
| Submission Date | Centered, near bottom, uppercase | Generation timestamp |
| Page Number | Bottom right, "CurrentPage \| TotalPages" | PDF footer |
| **Exclusions** | No institution, supervisor, abstract, logos | Validation layer |

### 2. TABLE OF CONTENTS (Image-Aligned)
| Element | Requirement | Implementation |
|---------|-------------|----------------|
| Title | "TABLE OF CONTENTS", centered, uppercase | PDF generation |
| Entries | Section title + dotted leader + page number | ReportLab paragraph |
| Hierarchy | Progressive indentation by level | Style configuration |
| Dot Leaders | Uniform dots, fill space | Custom paragraph style |
| Font | Same as body, no bold/italics | Style inheritance |

### 3. SUBSCRIPTION TIERS
| Tier | Preview | PDF Export | Watermark |
|------|---------|------------|-----------|
| Free | 300 words max | ❌ No | N/A |
| Non-permanent | Full | Preview only | "FOMA Digital Solution" |
| Permanent | Full | ✅ Clean | None |

### 4. NEW AGENT: Proofreading and Consistency Agent
| Responsibility | Action |
|----------------|--------|
| Title page validation | Check layout compliance |
| TOC validation | Check formatting compliance |
| Heading hierarchy | Ensure consistency |
| Pagination | Ensure continuity |
| References | Ensure single occurrence |
| Gap visualization | Request flow diagrams |

---

## 🏗️ IMPLEMENTATION PHASES

### Phase 1: Backend Enhancements
1. Add subscription tier to user model
2. Create Proofreading and Consistency Agent
3. Update PDF export with watermark logic
4. Implement title page template
5. Implement TOC generation

### Phase 2: Frontend Enhancements
1. Add subscription tier display
2. Implement preview word limit for free tier
3. Add watermark preview indicator
4. Update export buttons with tier logic
5. Enhanced UI/UX components

### Phase 3: Integration & Validation
1. End-to-end testing
2. Watermark verification
3. PDF layout validation
4. Performance optimization

---

## 📁 FILES TO MODIFY

### Backend (Minimal Changes)
- `src/api/main.py` - Add subscription logic, PDF watermark
- No new files required

### Frontend (Minimal Changes)
- `frontend/src/services/store.ts` - Add subscription state
- `frontend/src/pages/dashboard.tsx` - Add tier-based UI
- `frontend/src/services/api.ts` - Add subscription types

---

## ⚠️ STABILITY GUARANTEES

✅ No refactoring of existing code
✅ No renaming of files/folders
✅ No agent order changes (except new agent insertion)
✅ No new dependencies unless unavoidable
✅ Single deterministic application of changes
✅ No infinite correction loops

---
