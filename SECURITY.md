# Security Policy

## Our Commitment

The OpenInfra team takes the security of our software seriously. We appreciate your efforts to responsibly disclose your findings and will make every effort to acknowledge your contributions.

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

**Note**: Only the latest stable release receives security updates. We encourage all users to upgrade to the latest version.

---

## Reporting a Vulnerability

If you discover a security vulnerability in OpenInfra, please follow these guidelines:

### 🚨 DO NOT create a public GitHub issue for security vulnerabilities

Instead, please report security vulnerabilities through one of these channels:

### Option 1: GitHub Security Advisories (Recommended)

1. Go to the [Security tab](https://github.com/your-org/openinfra/security) in our repository
2. Click "Report a vulnerability"
3. Fill out the vulnerability report form
4. Submit the report

### Option 2: Email

Send an email to: **security@openinfra.example.com**

Please include:
- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it
- Your name/affiliation (if you wish to be credited)

### Option 3: Encrypted Communication

For highly sensitive security issues, you can use our PGP key to encrypt your message:

```
[PGP Key Fingerprint will be added here]
```

---

## What to Expect

### Response Timeline

- **Initial Response**: Within 48 hours of report submission
- **Status Update**: Within 5 business days
- **Resolution Timeline**: Depends on severity (see below)

### Severity Levels and Response Times

| Severity | Response Time | Example |
|----------|---------------|---------|
| **Critical** | 24-48 hours | Authentication bypass, SQL injection, remote code execution |
| **High** | 3-7 days | Privilege escalation, sensitive data exposure |
| **Medium** | 14-30 days | CSRF, XSS, information disclosure |
| **Low** | 30-90 days | Minor information disclosure, denial of service (local) |

### Our Process

1. **Acknowledgment**: We'll acknowledge receipt of your vulnerability report within 48 hours
2. **Assessment**: We'll investigate and confirm the vulnerability
3. **Fix Development**: We'll develop and test a fix
4. **Disclosure**: We'll coordinate disclosure timing with you
5. **Release**: We'll release the fix in a new version
6. **Credit**: We'll credit you in our security advisory (if desired)

---

## Security Best Practices

### For Users

#### Production Deployment

1. **Environment Variables**: Never commit `.env` files or hardcode secrets
   ```bash
   # Use environment variables
   SECRET_KEY=use-strong-random-key
   JWT_SECRET_KEY=use-different-strong-key
   ```

2. **Database Security**:
   - Use strong MongoDB passwords
   - Enable MongoDB authentication
   - Restrict MongoDB network access
   - Use TLS for database connections

3. **API Security**:
   - Enable rate limiting
   - Use HTTPS in production
   - Implement proper CORS policies
   - Keep JWT secrets secure and rotate regularly

4. **Infrastructure**:
   - Keep all dependencies up to date
   - Use Docker image scanning
   - Enable firewall rules
   - Regular security audits

#### Recommended .env Settings for Production

```bash
# Production Security Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=warning

# Strong secrets (generate with: openssl rand -hex 32)
SECRET_KEY=<generate-strong-random-key>
JWT_SECRET_KEY=<generate-strong-random-key>
JWT_EXPIRATION_MINUTES=60

# Database with authentication
MONGODB_URL=mongodb://username:strong_password@host:27017/db?authSource=admin

# Redis with password
REDIS_URL=redis://:strong_password@host:6379/0

# Secure MQTT
MQTT_USERNAME=secure_username
MQTT_PASSWORD=strong_password
```

### For Contributors

#### Code Security

1. **Input Validation**: Always validate and sanitize user input
   ```python
   # Good
   from pydantic import BaseModel, validator

   class AssetCreate(BaseModel):
       name: str

       @validator('name')
       def validate_name(cls, v):
           if len(v) < 3:
               raise ValueError('Name too short')
           return v
   ```

2. **SQL/NoSQL Injection Prevention**: Use parameterized queries
   ```python
   # Good (using Motor with proper query structure)
   await collection.find_one({"_id": ObjectId(asset_id)})

   # Bad (vulnerable to injection)
   await collection.find_one(eval(user_input))
   ```

3. **Authentication**: Never bypass authentication checks
   ```python
   # Good
   @router.get("/assets/{id}")
   async def get_asset(
       asset_id: str,
       current_user: User = Depends(get_current_user)
   ):
       ...
   ```

4. **Secrets Management**: Never hardcode secrets
   ```python
   # Bad
   API_KEY = "abc123xyz"

   # Good
   from app.core.config import settings
   API_KEY = settings.API_KEY
   ```

5. **Error Handling**: Don't expose sensitive information in errors
   ```python
   # Bad
   except Exception as e:
       raise HTTPException(500, detail=str(e))

   # Good
   except Exception as e:
       logger.error(f"Error: {e}")
       raise HTTPException(500, detail="Internal server error")
   ```

#### Dependency Security

1. **Keep Dependencies Updated**: Regularly update packages
   ```bash
   # Python
   pip list --outdated
   pip install --upgrade package_name

   # Node.js
   npm outdated
   npm update
   ```

2. **Audit Dependencies**: Check for known vulnerabilities
   ```bash
   # Python
   pip install safety
   safety check

   # Node.js
   npm audit
   npm audit fix
   ```

3. **Use Lock Files**: Commit lock files to ensure reproducible builds
   - `requirements.txt` (Python)
   - `package-lock.json` or `pnpm-lock.yaml` (Node.js)

---

## Security Features

### Built-in Security

OpenInfra includes several security features by default:

1. **Authentication & Authorization**:
   - JWT-based authentication
   - Role-based access control (RBAC)
   - Permission-based authorization
   - Secure password hashing (bcrypt)

2. **API Security**:
   - Rate limiting
   - CORS protection
   - Request validation (Pydantic)
   - SQL injection prevention
   - XSS protection

3. **Data Protection**:
   - Encrypted passwords
   - Secure session management
   - Audit logging
   - Data validation

4. **Infrastructure Security**:
   - TLS/SSL support
   - Secure headers
   - Environment-based configuration
   - Docker security best practices

---

## Known Security Considerations

### Current Limitations

1. **Multi-factor Authentication (MFA)**: Not yet implemented
   - **Workaround**: Use strong passwords and short token expiration times

2. **API Key Rotation**: Manual process
   - **Recommendation**: Rotate API keys regularly

3. **File Upload Validation**: Basic validation only
   - **Recommendation**: Implement additional virus scanning in production

### Roadmap

Planned security improvements:
- [ ] Two-factor authentication (2FA)
- [ ] API key rotation mechanism
- [ ] Advanced file upload scanning
- [ ] Security audit logging dashboard
- [ ] Automated dependency vulnerability scanning
- [ ] Penetration testing

---

## Security Updates

### How We Communicate Security Updates

1. **GitHub Security Advisories**: Primary channel for security announcements
2. **Release Notes**: Security fixes mentioned in CHANGELOG.md
3. **Email**: Critical security updates sent to registered users (future feature)

### Subscribing to Security Updates

- Watch this repository on GitHub
- Enable "Security alerts" in your GitHub notification settings
- Check our [Security Advisories page](https://github.com/your-org/openinfra/security/advisories)

---

## Bounty Program

Currently, OpenInfra does not have a formal bug bounty program. However:

- We deeply appreciate security researchers' efforts
- We will credit you in our security advisory (if desired)
- We may offer recognition on our website/repository
- We're working on establishing a formal bounty program

---

## Security Checklist for Deployment

Before deploying to production, ensure:

- [ ] All secrets are stored in environment variables (not in code)
- [ ] `.env` files are in `.gitignore`
- [ ] Strong, unique passwords for all services
- [ ] JWT secret keys are randomly generated
- [ ] HTTPS/TLS is enabled
- [ ] Database authentication is enabled
- [ ] Rate limiting is configured
- [ ] CORS is properly configured
- [ ] Latest security patches are applied
- [ ] Dependency vulnerabilities are resolved
- [ ] Logging and monitoring are enabled
- [ ] Backups are configured and tested
- [ ] Firewall rules are in place
- [ ] Security headers are configured

---

## Hall of Fame

We'd like to thank the following security researchers for responsibly disclosing vulnerabilities:

<!--
Format:
- **[Your Name](your-website)** - Description of vulnerability (Date)
-->

*No entries yet. Be the first!*

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [MongoDB Security Checklist](https://docs.mongodb.com/manual/administration/security-checklist/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---

## Questions?

If you have questions about security:
- Non-sensitive questions: [GitHub Discussions](https://github.com/your-org/openinfra/discussions)
- Security-related questions: security@openinfra.example.com

---

## Legal

By reporting security vulnerabilities to us, you agree that:
- You will not publicly disclose the issue until we've had a chance to address it
- You will not exploit the vulnerability beyond what is necessary to demonstrate it
- You are reporting the vulnerability in good faith
- Your actions comply with all applicable laws

We commit to:
- Not pursue legal action against researchers who follow this policy
- Work with you to understand and resolve the issue quickly
- Credit you for your discovery (if desired)

---

**Last Updated**: December 2024

Thank you for helping keep OpenInfra and our users safe! 🔒
