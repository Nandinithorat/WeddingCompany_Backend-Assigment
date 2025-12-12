# Organization Management Service

A multi-tenant backend service built with FastAPI and MongoDB. Each organization gets its own collection for data isolation.

## Why I Built It This Way

So I went with FastAPI because it's fast (obviously), has great auto-docs, and handles async stuff really well. MongoDB made sense here since we're doing dynamic collection creation - it's way easier than dealing with SQL schemas for each tenant.

### Project Structure

```
org-management/
├── main.py              # App initialization, startup events
├── config.py            # Environment vars and constants
├── database.py          # MongoDB connection and setup
├── models.py            # Request/response schemas
├── auth.py              # JWT and password handling
├── services.py          # Core business logic
├── routes.py            # API endpoint definitions
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

I split everything into modules to keep it clean. Each file has a specific job - routes handle HTTP stuff, services contain the actual logic, auth deals with tokens and passwords, etc.

## Setup & Installation

### Prerequisites
- Python 3.8+
- MongoDB running locally (default port 27017)

### Quick Start

1. Clone and setup:
```bash
git clone <your-repo-url>
cd org-management
pip install -r requirements.txt
```

2. (Optional) Set environment variables:
```bash
export SECRET_KEY="your-super-secret-key"
export MONGODB_URI="mongodb://localhost:27017/"
```

3. Start MongoDB if not running:
```bash
mongod
```

4. Run the application:
```bash
uvicorn main:app --reload
```

5. Check it's working:
```
http://localhost:8000/docs
```

The `/docs` endpoint gives you a Swagger UI to test everything.

## API Endpoints

### 1. Create Organization
**POST** `/org/create`

Creates a new organization with its own collection and admin user.

```json
{
  "organization_name": "acme_corp",
  "email": "admin@acme.com",
  "password": "secure_password123"
}
```

**What happens:**
- Checks if org name or email already exists
- Creates a new MongoDB collection (like `org_acme_corp`)
- Hashes the password with bcrypt
- Stores org metadata in master database
- Returns org details

**Response:**
```json
{
  "success": true,
  "message": "Org created",
  "data": {
    "organization_id": "...",
    "organization_name": "acme_corp",
    "collection_name": "org_acme_corp",
    "admin_email": "admin@acme.com",
    "created_at": "2024-12-12T10:30:00"
  }
}
```

### 2. Get Organization
**GET** `/org/get?organization_name=acme_corp`

Fetches organization details from master database.

**Response:**
```json
{
  "success": true,
  "data": {
    "organization_id": "...",
    "organization_name": "acme_corp",
    "collection_name": "org_acme_corp",
    "admin_email": "admin@acme.com",
    "created_at": "2024-12-12T10:30:00",
    "connection_details": {
      "database": "master_organization_db",
      "collection": "org_acme_corp"
    }
  }
}
```

### 3. Update Organization
**PUT** `/org/update`

Updates org name and/or admin credentials. If name changes, it migrates data to new collection.

```json
{
  "organization_name": "acme_corp",
  "new_organization_name": "acme_industries",
  "email": "newadmin@acme.com",
  "password": "new_password123"
}
```

**What happens:**
- Finds the org
- If name changed: creates new collection, copies all data, drops old one
- Updates admin email/password if provided
- Updates org metadata

### 4. Delete Organization
**DELETE** `/org/delete`

**Requires Authentication** - Bearer token in header

```json
{
  "organization_name": "acme_corp"
}
```

**Header:**
```
Authorization: Bearer <your-jwt-token>
```

**What happens:**
- Verifies you're the admin of this org
- Drops the organization collection
- Deletes admin user
- Removes org from master database

### 5. Admin Login
**POST** `/admin/login`

```json
{
  "email": "admin@acme.com",
  "password": "secure_password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "admin_id": "...",
  "organization_id": "...",
  "organization_name": "acme_corp"
}
```

Token expires in 30 minutes. Use it in the Authorization header for protected routes.

## Architecture Decisions

### Why This Design?

**Multi-tenant with Collection-per-Tenant:**
I went with a collection-per-tenant approach instead of shared collections with tenant filters. Here's why:

**Pros:**
- Data isolation is straightforward - each org literally has its own collection
- Easy to backup/restore individual orgs
- Performance doesn't degrade as you add more orgs (no filtering needed)
- Can drop an org's data instantly without complex queries
- Simpler queries - no need to always filter by org_id

**Cons:**
- MongoDB has collection limits (though it's pretty high)
- Can't easily do cross-organization analytics
- More collections = more overhead (but minimal with Mongo)

### Tech Stack Choices

**FastAPI:**
- Built-in validation with Pydantic
- Auto-generated API docs
- Fast performance
- Async support (though not fully utilized here)

**MongoDB:**
- Schema-less makes dynamic collection creation easy
- Good for this multi-tenant pattern
- Scales horizontally well
- No migrations needed when adding fields

**JWT Authentication:**
- Stateless - no session storage needed
- Token contains all needed info
- Easy to scale across servers

**bcrypt:**
- Industry standard for password hashing
- Salted automatically
- Configurable work factor

### What Could Be Better?

**Current Issues:**

1. **No Rate Limiting** - Anyone can hammer the API right now. Should add something like SlowAPI.

2. **Error Handling** - It's basic. Production would need better error messages and logging.

3. **No Validation on Collection Names** - Some org names could create weird collection names. Need better sanitization.

4. **Password Requirements** - Just checking length. Should enforce complexity.

5. **No Refresh Tokens** - Tokens expire in 30min. Should implement refresh token flow.

6. **Missing Features:**
   - Password reset
   - Email verification
   - Admin role management (what if org needs multiple admins?)
   - Audit logging

**Better Architecture for Scale:**

If this needed to handle thousands of orgs, I'd consider:

1. **Separate Databases per Org** - Instead of collections, give each org its own database. Better isolation, easier to shard.

2. **Cache Layer** - Add Redis for:
   - Token blacklist (for logout)
   - Rate limiting
   - Org metadata caching

3. **Message Queue** - For async operations like:
   - Sending welcome emails
   - Data migrations
   - Cleanup tasks

4. **API Gateway** - For rate limiting, request routing, and load balancing.

5. **Proper Logging** - ELK stack or similar for debugging and monitoring.

**Alternative: Shared Database Approach**

Could also do:
```
organizations_collection
users_collection (with org_id)
data_collection (with org_id, properly indexed)
```

**Pros:** Simpler structure, easier cross-org queries
**Cons:** Need careful indexing, queries always need org_id, data mixing risk

I stuck with collection-per-tenant because the assignment mentioned "dynamic collections" and it fits the multi-tenant requirement better.

## Security Considerations

What's implemented:
- Password hashing with bcrypt
- JWT tokens for auth
- Protected delete endpoint
- Input validation via Pydantic

What's missing:
- HTTPS/SSL (should be handled by reverse proxy)
- Rate limiting
- SQL injection protection (MongoDB handles this)
- CORS configuration
- Request size limits
- Token refresh mechanism

## Database Schema

**Master Database Collections:**

**organizations:**
```javascript
{
  _id: ObjectId,
  organization_name: "acme_corp",
  collection_name: "org_acme_corp",
  admin_id: "admin_object_id",
  admin_email: "admin@acme.com",
  created_at: ISODate,
  connection_details: {
    database: "master_organization_db",
    collection: "org_acme_corp"
  }
}
```

**admins:**
```javascript
{
  _id: ObjectId,
  email: "admin@acme.com",
  password: "$2b$12$hashed_password",
  created_at: ISODate
}
```

**org_<name> (per organization):**
```javascript
{
  _id: ObjectId,
  initialized: true,
  created_at: ISODate,
  note: "Org data goes here"
  // ... org-specific data
}
```

## Testing

Quick test flow:

```bash
# 1. Create an organization
curl -X POST http://localhost:8000/org/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "test_corp",
    "email": "admin@test.com",
    "password": "password123"
  }'

# 2. Login
curl -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "password123"
  }'

# Copy the access_token from response

# 3. Get org details
curl http://localhost:8000/org/get?organization_name=test_corp

# 4. Delete org (needs token)
curl -X DELETE http://localhost:8000/org/delete \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "test_corp"}'
```

Or just use the Swagger UI at `/docs` - way easier.

## Common Issues

**MongoDB Connection Failed:**
- Make sure MongoDB is running: `mongod`
- Check the connection string in config.py
- Default is `mongodb://localhost:27017/`

**Import Errors:**
- Install dependencies: `pip install -r requirements.txt`
- Check Python version (needs 3.8+)

**Token Issues:**
- Tokens expire after 30 minutes
- Make sure you're passing it in headers: `Authorization: Bearer <token>`
- Check the token format

**Collection Already Exists:**
- If you get errors about collections, might need to clean up MongoDB
- Use `mongo` shell: `db.dropDatabase()` to reset

## What I'd Do Next

If I had more time:

1. Add proper unit tests (pytest)
2. Docker setup for easy deployment
3. Environment-based configs (dev/staging/prod)
4. Better logging with proper log levels
5. API versioning (/v1/org/create)
6. Pagination for list endpoints
7. Search/filter functionality
8. Soft delete instead of hard delete
9. Admin dashboard (separate frontend)
10. Metrics and monitoring

## Notes

- The code is modular but kept simple for clarity
- Used standard Python naming conventions
- Comments are minimal on purpose - code should be self-documenting
- No over-engineering - meets requirements without extra complexity
- Production deployment would need more hardening

Built this over a weekend, so there's definitely room for improvements but it covers all the requirements in the assignment.

---

Feel free to reach out if you have questions or find issues!