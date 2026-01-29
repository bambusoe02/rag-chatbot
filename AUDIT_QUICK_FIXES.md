# Quick Fixes - Critical Issues

**Priority: Fix these BEFORE production deployment**

## 🔴 CRITICAL (Fix Immediately - 2-3 hours)

### 1. SECRET_KEY Validation (10 min)
**File:** `backend/auth.py:15`

**Current:**
```python
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-use-openssl-rand-hex-32")
```

**Fix:**
```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError("SECRET_KEY must be set in production environment")
    # Only allow weak default in development
    SECRET_KEY = "dev-secret-key-change-in-production"
    logger.warning("⚠️  Using default SECRET_KEY - NOT SAFE FOR PRODUCTION")
```

---

### 2. Docker Compose SECRET_KEY (5 min)
**File:** `docker-compose.yml:31`

**Current:**
```yaml
- SECRET_KEY=${SECRET_KEY:-change-this-in-production}
```

**Fix:**
```yaml
- SECRET_KEY=${SECRET_KEY}  # Remove default, must be set
```

**And add validation in startup:**
```python
if not os.getenv("SECRET_KEY") or os.getenv("SECRET_KEY") == "change-this-in-production":
    raise ValueError("SECRET_KEY must be set in environment variables")
```

---

### 3. Add email_validator Dependency (2 min)
**File:** `requirements.txt`

**Add:**
```txt
email_validator==2.1.1
```

**Then run:**
```bash
pip install email_validator==2.1.1
```

---

### 4. Make CORS Configurable (15 min)
**File:** `backend/main.py:43`

**Current:**
```python
allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
```

**Fix:**
```python
import os

# Get CORS origins from environment variable
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 5. Replace print() Statements (30 min)
**Files to fix:**
- `frontend/utils/i18n.py:32`
- `frontend/utils/file_handler.py:41,59,80,98,137,151`
- `frontend/pages/2_🔑_API_Keys.py:178,206`
- `frontend/pages/3_🔔_Webhooks.py:207,209`

**Replace:**
```python
print(f"Error: {e}")
```

**With:**
```python
# For Streamlit pages:
st.error(f"Error: {e}")

# For utility modules:
from loguru import logger
logger.error(f"Error: {e}")
```

---

### 6. Review English Text (10 min)
**Files to check:**
- `README.md:378` - Location info is OK, but ensure all functional text is English
- `docs/user/README.md:63` - "Polski" reference

**Action:** Review all user-facing text, ensure it's in English (location mentions like "Warsaw, Poland" are OK)

---

## ✅ COMPLETED

- ✅ `.env.example` created - **DONE**

---

## 📋 Verification Checklist

After fixes, verify:

- [ ] SECRET_KEY validation works (try running without SECRET_KEY set)
- [ ] `email_validator` installed and imports work
- [ ] CORS allows your production domain
- [ ] No `print()` statements in code (grep for "print(")
- [ ] All user-facing text is in English
- [ ] `.env.example` exists and is complete

---

## 🚀 Quick Test

```bash
# 1. Test SECRET_KEY validation
unset SECRET_KEY
python -c "from backend.auth import SECRET_KEY; print('FAIL' if 'change-in-production' in SECRET_KEY else 'PASS')"

# 2. Test email_validator
python -c "from pydantic import EmailStr; print('PASS')"

# 3. Check for print statements
grep -r "print(" frontend/ --include="*.py" | grep -v "#" | wc -l
# Should be 0

# 4. Verify .env.example exists
test -f .env.example && echo "PASS" || echo "FAIL"
```

---

**Total Time:** 2-3 hours for all critical fixes

