// scratch/shared/src/users.rs
// User API module using Actix-web + SQLx (PostgreSQL)
// Endpoints:
//  - GET /users
//  - POST /users
//  - GET /users/{id}
//
// Includes:
//  - Validation for input payloads
//  - Placeholder authentication middleware (Bearer token)
//  - Error handling patterns and a migrations outline
//  - User model with id, name, email, created_at

use actix_web::{web, HttpResponse, Responder, HttpRequest, Error as ActixError};
use sqlx::PgPool;
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::sync::Arc;
use regex::Regex;
use once_cell::sync::Lazy;

// --------------------
// MIGRATIONS OUTLINE
// --------------------
// The following SQL outlines the initial migration to create the users table.
// This should be placed in a migrations/ directory with proper tooling (sqlx migrate).
//
// Migration: create_users_table
// -- Up
// CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- enable UUID generation (or use gen_random_uuid())
// CREATE TABLE IF NOT EXISTS users (
//   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
//   name VARCHAR(255) NOT NULL,
//   email VARCHAR(255) NOT NULL UNIQUE,
//   created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
// );
//
// -- Down
// DROP TABLE IF EXISTS users;
// --------------------

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct User {
    pub id: Uuid,
    pub name: String,
    pub email: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct NewUser {
    pub name: String,
    pub email: String,
}

#[derive(Debug, Serialize)]
pub struct UserResponse {
    pub id: String,
    pub name: String,
    pub email: String,
    pub created_at: String,
}

impl From<User> for UserResponse {
    fn from(u: User) -> Self {
        UserResponse {
            id: u.id.to_string(),
            name: u.name,
            email: u.email,
            created_at: u.created_at.to_rfc3339(),
        }
    }
}

// Validation regex for basic email format checking (very lightweight)
static EMAIL_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^[^\s@]+@[^\s@]+\.[^\s@]+$").unwrap()
});

static NAME_MIN_LEN: usize = 1;

fn validate_new_user(input: &NewUser) -> Result<(), Vec<String>> {
    let mut errors: Vec<String> = Vec::new();
    if input.name.trim().len() < NAME_MIN_LEN {
        errors.push("name_required".to_string());
    }
    if !EMAIL_REGEX.is_match(&input.email) {
        errors.push("email_invalid".to_string());
    }
    if errors.is_empty() { Ok(()) } else { Err(errors) }
}

// --------------------
// Authentication placeholder middleware
// --------------------
use actix_service::{Service, Transform};
use actix_web::dev::{ServiceRequest, ServiceResponse, Payload};
use actix_web::http::StatusCode;
use futures_util::future::{LocalBoxFuture, Ready, ready};
use std::task::{Context, Poll};

pub struct AuthGuard;

impl<S, B> Transform<S> for AuthGuard
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = ActixError> + 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = ActixError;
    type Transform = AuthGuardMiddleware<S>;
    type InitError = ();
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        ready(Ok(AuthGuardMiddleware { service }))
    }
}

pub struct AuthGuardMiddleware<S> {
    service: S,
}

impl<S, B> Service<ServiceRequest> for AuthGuardMiddleware<S>
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = ActixError> + 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = ActixError;
    type Future = LocalBoxFuture<'static, Result<Self::Response, Self::Error>>;

    fn poll_ready(&mut self, cx: &mut std::task::Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.service.poll_ready(cx)
    }

    fn call(&mut self, req: ServiceRequest) -> Self::Future {
        // Simple placeholder: require Authorization header with Bearer token
        let token_ok = {
            if let Some(header_value) = req.headers().get(actix_web::http::header::AUTHORIZATION) {
                if let Ok(s) = header_value.to_str() {
                    if s.starts_with("Bearer ") {
                        let token = &s[7..];
                        // Accept a hard-coded token or an env var override
                        let env_token = std::env::var("AUTH_TOKEN").ok();
                        if token == "test-token" || env_token.as_deref() == Some(token) {
                            true
                        } else {
                            false
                        }
                    } else {
                        false
                    }
                } else {
                    false
                }
            } else {
                false
            }
        };

        if token_ok {
            let fut = self.service.call(req);
            Box::pin(async move {
                let res = fut.await?;
                Ok(res)
            })
        } else {
            Box::pin(async {
                let resp = HttpResponse::Unauthorized()
                    .json(serde_json::json!({"error": "unauthorized"}));
                Ok(req.into_response(resp.into_body()))
            })
        }
    }
}

// --------------------
// Route configuration
// --------------------
pub fn config(cfg: &mut web::ServiceConfig) {
    // Routes under /users
    cfg.service(
        web::scope("/users")
            .wrap(AuthGuard)
            .route("/", web::get(list_users).post(create_user))
            .route("/{id}", web::get(get_user)),
    );
}

// --------------------
// Handlers
// --------------------
async fn list_users(state: web::Data<AppState>) -> Result<HttpResponse, ActixError> {
    let pool = &state.db_pool;
    let rows = sqlx::query_as::<_, User>(
        "SELECT id, name, email, created_at FROM users ORDER BY created_at DESC",
    )
    .fetch_all(pool)
    .await
    .map_err(|e| ActixError::from(e))?;

    let resp: Vec<UserResponse> = rows.into_iter().map(UserResponse::from).collect();
    Ok(HttpResponse::Ok().json(resp))
}

#[derive(Clone)]
pub struct AppState {
    pub db_pool: PgPool,
}

async fn get_user(state: web::Data<AppState>, path: web::Path<Uuid>) -> Result<HttpResponse, ActixError> {
    let pool = &state.db_pool;
    let id = path.into_inner();
    let row = sqlx::query_as::<_, User>(
        "SELECT id, name, email, created_at FROM users WHERE id = $1",
    )
    .bind(id)
    .fetch_one(pool)
    .await
    .map_err(|e| {
        if let sqlx::Error::RowNotFound = e {
            ActixError::from(HttpResponse::NotFound().json(serde_json::json!({"error": "not_found"})))
        } else {
            ActixError::from(e)
        }
    })?;

    let resp = UserResponse::from(row);
    Ok(HttpResponse::Ok().json(resp))
}

async fn create_user(state: web::Data<AppState>, payload: web::Json<NewUser>) -> Result<HttpResponse, ActixError> {
    // Validate input
    match validate_new_user(&payload) {
        Ok(()) => {},
        Err(errors) => {
            return Ok(HttpResponse::BadRequest().json(serde_json::json!({
                "error": "validation_failed",
                "details": errors,
            })));
        }
    }

    let pool = &state.db_pool;
    let new = payload.into_inner();
    // Insert and return created user
    let row = sqlx::query_as::<_, User>(
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id, name, email, created_at",
    )
    .bind(new.name)
    .bind(new.email)
    .fetch_one(pool)
    .await
    .map_err(|e| ActixError::from(e))?;

    let resp = UserResponse::from(row);
    Ok(HttpResponse::Created().json(resp))
}

// --------------------
// Tests (focused on validation and small helpers)
// --------------------
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_new_user_valid() {
        let input = NewUser { name: "Alice".to_string(), email: "alice@example.com".to_string() };
        assert!(validate_new_user(&input).is_ok());
    }

    #[test]
    fn test_validate_new_user_invalid() {
        let input = NewUser { name: "".to_string(), email: "not-an-email".to_string() };
        let res = validate_new_user(&input);
        assert!(res.is_err());
        let errs = res.unwrap_err();
        assert!(errs.iter().any(|e| e == "name_required"));
        assert!(errs.iter().any(|e| e == "email_invalid"));
    }
}
