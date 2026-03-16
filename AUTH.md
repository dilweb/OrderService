# Auth Module

JWT-based authentication with access/refresh token pair. Tokens delivered via `httponly` cookies and response body.

## Token Types

| Type | TTL | Purpose |
|---|---|---|
| `access` | 15 min | Authorization header / cookie |
| `refresh` | 7 days | Renewing token pair |
| `email_verification` | 24 h | Email confirmation on register |
| `password_reset` | 1 h | Password reset via email |

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register/` | — | Register, sends verification email |
| GET | `/auth/verify-email?token=` | — | Confirm email, sets cookies |
| POST | `/auth/login/` | — | Returns `access_token` + `refresh_token` |
| POST | `/auth/logout/` | — | Clears cookies |
| POST | `/auth/refresh/` | — | Refresh pair (cookie or body) |
| GET | `/auth/me/` | user | Current user info |
| POST | `/auth/password/forgot/` | — | Request password reset token |
| POST | `/auth/password/reset/` | — | Reset password by token |
| POST | `/auth/password/change/` | user | Change password (requires old password) |
| GET | `/auth/get-user/{id}/` | admin | Get user by ID |
| PATCH | `/auth/make-admin/{user_id}/` | super_admin | Grant admin role |
| GET | `/auth/users/` | admin | List all users |
| DELETE | `/auth/users/delete-my-account/` | user | Delete own account |
| DELETE | `/auth/users/{user_id}/` | user/super_admin | Delete account (own or any) |

## Role System

```
is_user < is_admin < is_super_admin
```

Dependencies: `get_current_user` → `get_current_admin_user` → `get_current_super_admin_user`

## Token Extraction (`get_token`)

1. `Authorization: Bearer <token>` header
2. `users_access_token` cookie

## Password Hashing

`bcrypt` via `passlib.CryptContext`.
