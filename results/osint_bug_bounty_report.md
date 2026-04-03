# OSINT Report: Bug Bounty Programs for Xinference & MiniRAG

**Research Date:** 2026-04-02  
**Analyst:** Qwen Code Security Agent  
**Scope:** Global Bug Bounty Platforms + VDP Programs

---

## Executive Summary

| Target | Vendor | Bug Bounty Status | VDP Status |
|--------|--------|-------------------|------------|
| **Xinference** | Xorbits (xorbitsai) | ❌ Not Found | ⚠️ GitHub Issues Only |
| **MiniRAG** | HKUDS (HKU) | ❌ Not Found | ❌ Not Found |

---

## 1. Platform Search Results

### HackerOne
**Search Query:** `site:hackerone.com "xorbits" OR "xinference"`  
**Result:** ❌ **No programs found**

**Search Query:** `site:hackerone.com "hkuds" OR "minirag"`  
**Result:** ❌ **No programs found**

---

### Bugcrowd
**Search Query:** `site:bugcrowd.com "xorbits" OR "xinference"`  
**Result:** ❌ **No programs found**

**Search Query:** `site:bugcrowd.com "hkuds" OR "minirag"`  
**Result:** ❌ **No programs found**

---

### Intigriti
**Search Query:** `site:intigriti.com "xorbits" OR "xinference"`  
**Result:** ❌ **No programs found**

**Search Query:** `site:intigriti.com "hkuds" OR "minirag"`  
**Result:** ❌ **No programs found**

---

### YesWeHack
**Search Query:** `site:yeswehack.com "xorbits" OR "xinference"`  
**Result:** ❌ **No programs found**

**Search Query:** `site:yeswehack.com "hkuds" OR "minirag"`  
**Result:** ❌ **No programs found**

---

### Huntr.com (AI/ML Specific)
**Search Query:** `site:huntr.com "xorbitsai/inference" OR "xinference"`  
**Result:** ⚠️ **Indirect mentions only** (user profiles, not official program)

**Search Query:** `site:huntr.com "HKUDS/MiniRAG" OR "MiniRAG"`  
**Result:** ❌ **No official program found**

**Note:** Huntr.com has an AI/ML bug bounty program, but neither Xinference nor MiniRAG have dedicated program pages.

---

## 2. Corporate VDP (Vulnerability Disclosure Policy) Search

### Xorbits (xorbits.io)

**Search Queries:**
- `"xorbits" "bug bounty"`
- `"xorbits" "vulnerability disclosure"`
- `"xinference" "report vulnerability"`
- `"xinference" "security policy"`

**Results:**

| Channel | Status | Details |
|---------|--------|---------|
| **security.txt** | ❌ Not Found | `https://xorbits.io/.well-known/security.txt` returns 403 Forbidden |
| **GitHub SECURITY.md** | ❌ Not Found | `github.com/xorbitsai/inference/security` shows "No security policy detected" |
| **Direct Email** | ❌ Not Found | No security@ or security-contact email found |
| **GitHub Issues** | ⚠️ Informal | Vulnerabilities reported via regular GitHub Issues |

**Official Channels:**
- GitHub Issues: https://github.com/xorbitsai/inference/issues
- No dedicated security contact identified

---

### HKUDS (HKU Data Science)

**Search Queries:**
- `"HKUDS" "bug bounty"`
- `"HKUDS" "vulnerability disclosure"`
- `"MiniRAG" "security policy"`
- `"MiniRAG" "report vulnerability"`

**Results:**

| Channel | Status | Details |
|---------|--------|---------|
| **security.txt** | ❌ Not Found | No security.txt found for HKUDS domains |
| **GitHub SECURITY.md** | ❌ Not Found | `github.com/HKUDS/MiniRAG` has no SECURITY.md |
| **Direct Email** | ❌ Not Found | No security contact email found |
| **GitHub Issues** | ⚠️ Informal | Bugs reported via GitHub Issues only |

**Official Channels:**
- GitHub Issues: https://github.com/HKUDS/MiniRAG/issues
- No dedicated security contact identified

---

## 3. Security.txt Analysis

### xorbits.io

**Attempted URLs:**
- `https://xorbits.io/.well-known/security.txt` → **403 Forbidden**
- `https://xorbits.io/security.txt` → **Not Found**

**Conclusion:** No standardized security contact mechanism in place.

---

### HKUDS (hku.hk / hkuspace.hku.hk)

**Attempted URLs:**
- `https://www.hku.hk/.well-known/security.txt` → **Not Found**
- `https://www.hku.hk/security.txt` → **Not Found**

**Conclusion:** No standardized security contact mechanism in place.

---

## 4. Alternative Disclosure Channels

### For Xinference (Xorbits)

| Method | URL | Type | Bounty |
|--------|-----|------|--------|
| **GitHub Issues** | https://github.com/xorbitsai/inference/issues | Public | ❌ No |
| **GitHub Security Advisories** | https://github.com/xorbitsai/inference/security/advisories | Private | ❌ No |
| **Direct Email** | Not found | N/A | N/A |

---

### For MiniRAG (HKUDS)

| Method | URL | Type | Bounty |
|--------|-----|------|--------|
| **GitHub Issues** | https://github.com/HKUDS/MiniRAG/issues | Public | ❌ No |
| **GitHub Security Advisories** | https://github.com/HKUDS/MiniRAG/security/advisories | Private | ❌ No |
| **Direct Email** | Not found | N/A | N/A |

---

## 5. Historical Context

### Xinference Security History

**Known Vulnerabilities (via GitHub Issues):**
- Issue #1651: "BUG fix security vulnerability" (2024-06-16)
- Issue #3073: Authentication issues (2025-03-16)
- Multiple security-related issues reported via GitHub Issues

**Pattern:** Security vulnerabilities are handled through **public GitHub Issues**, not private disclosure channels.

---

### MiniRAG Security History

**Known Issues:**
- No dedicated security advisories found
- General bug reports via GitHub Issues
- Research project (HKU Data Science) - limited security infrastructure

**Pattern:** Academic/research project with **informal vulnerability handling**.

---

## 6. Recommendations for Researchers

### If You Find a Vulnerability in Xinference:

1. **Check if already reported:**
   - Search GitHub Issues: https://github.com/xorbitsai/inference/issues?q=is%3Aissue+security

2. **Report via GitHub Issues (Public):**
   - Create issue with `[Security]` tag
   - Provide detailed reproduction steps
   - Wait for maintainer response

3. **Report via GitHub Security Advisories (Private):**
   - Go to: https://github.com/xorbitsai/inference/security/advisories
   - Click "Report a vulnerability"
   - Submit privately to maintainers

4. **Consider Huntr.com:**
   - Even without official program, Huntr accepts AI/ML reports
   - May qualify for bounty if accepted

---

### If You Find a Vulnerability in MiniRAG:

1. **Check existing issues:**
   - https://github.com/HKUDS/MiniRAG/issues

2. **Report via GitHub Issues:**
   - Create detailed issue with `[Security]` or `[Bug]` tag
   - Include PoC and impact assessment

3. **Contact HKU Data Science directly:**
   - No formal security contact found
   - Try general HKU CS department email

4. **Consider Huntr.com:**
   - Submit as unsolicited report
   - May not qualify for bounty without official program

---

## 7. Bounty Eligibility Assessment

| Target | Huntr Eligible | Direct Bounty | CVE Attribution |
|--------|----------------|---------------|-----------------|
| **Xinference** | ⚠️ Maybe (case-by-case) | ❌ No | ✅ Yes (via GitHub) |
| **MiniRAG** | ⚠️ Maybe (case-by-case) | ❌ No | ✅ Yes (via GitHub) |

**Notes:**
- Huntr.com accepts AI/ML vulnerabilities even without official programs
- CVE attribution available via GitHub Security Advisories
- No monetary bounties expected (VDP only)

---

## 8. Conclusion

### Key Findings:

1. **No Official Bug Bounty Programs** found on major platforms (HackerOne, Bugcrowd, Intigriti, YesWeHack, Huntr)

2. **No Formal VDP** (Vulnerability Disclosure Policy) found for either vendor

3. **GitHub Issues** is the primary channel for vulnerability reporting

4. **No security.txt** files found for either organization

5. **Academic/Open-Source Nature:** Both projects are open-source/research with limited security infrastructure

---

### Best Disclosure Path:

**For Paid Bounties:**
- Submit to Huntr.com (AI/ML program) - acceptance not guaranteed
- No guarantee of payment without official program

**For CVE Attribution:**
- Use GitHub Security Advisories (private reporting)
- Request CVE via GitHub's CNA authority

**For Responsible Disclosure:**
- GitHub Issues (public) for non-critical issues
- GitHub Security Advisories (private) for critical issues

---

## 9. References

- Huntr.com AI/ML Program: https://huntr.com/bounties
- GitHub Security Advisories: https://docs.github.com/en/code-security/security-advisories
- security.txt Standard: https://securitytxt.org/
- CWE-1068: Inconsistent Security Policy: https://cwe.mitre.org/data/definitions/1068.html

---

**Report Generated:** 2026-04-02  
**Analyst:** Qwen Code Security Agent  
**Status:** Complete - No official bounty programs found
