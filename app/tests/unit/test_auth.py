"""
Unit tests for authentication endpoints and JWT handling.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from fastapi.testclient import TestClient

from app.models.models import User, UserRole
from app.auth.jwt_handler import create_access_token, verify_token


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_new_user(self, client: TestClient):
        """Test user registration with valid data."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "role": "user"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "hashed_password" not in data
        assert data["role"] == "user"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """Test registration with existing username fails."""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with existing email fails."""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, client: TestClient, test_user: User):
        """Test login with valid credentials."""
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: TestClient, test_user: User):
        """Test login with invalid credentials."""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, client: TestClient, auth_headers: dict):
        """Test getting current user with valid token."""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "role" in data

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_update_current_user(self, client: TestClient, auth_headers: dict):
        """Test updating current user information."""
        update_data = {
            "email": "updated@example.com"
        }
        
        response = client.put("/auth/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == update_data["email"]


class TestJWTHandler:
    """Test JWT token handling functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_data = {
            "sub": 1,
            "username": "testuser",
            "role": "user"
        }
        
        token = create_access_token(data=user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Test token verification with valid token."""
        user_data = {
            "sub": 1,
            "username": "testuser",
            "role": "user"
        }
        
        token = create_access_token(data=user_data)
        payload = verify_token(token)
        
        assert payload["sub"] == user_data["sub"]
        assert payload["username"] == user_data["username"]
        assert payload["role"] == user_data["role"]

    def test_verify_invalid_token(self):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(Exception):
            verify_token(invalid_token)

    def test_verify_expired_token(self):
        """Test token verification with expired token."""
        from datetime import timedelta
        
        user_data = {"sub": 1, "username": "testuser", "role": "user"}
        
        # Create token that expires immediately
        token = create_access_token(
            data=user_data, 
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(Exception):
            verify_token(token)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        from app.auth.jwt_handler import get_password_hash, verify_password
        
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False