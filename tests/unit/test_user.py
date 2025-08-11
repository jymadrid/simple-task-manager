"""
Unit tests for User model
"""

import pytest
from datetime import datetime, timedelta
from taskforge.core.user import User, UserRole, Permission, UserProfile


class TestUser:
    """Test cases for User model"""
    
    def test_user_creation(self):
        """Test basic user creation"""
        user = User.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.DEVELOPER
        assert user.is_active
        assert not user.is_verified
        assert len(user.id) > 0
        assert isinstance(user.created_at, datetime)
        assert user.password_hash != "password123"  # Should be hashed
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        user = User.create_user(
            username="testuser",
            email="test@example.com", 
            password="password123"
        )
        
        # Password should be hashed
        assert user.password_hash != "password123"
        
        # Should verify correct password
        assert user.verify_password("password123")
        
        # Should not verify incorrect password
        assert not user.verify_password("wrongpassword")
    
    def test_user_roles(self):
        """Test user role functionality"""
        # Test different roles
        admin = User.create_user("admin", "admin@example.com", "pass", role=UserRole.ADMIN)
        manager = User.create_user("manager", "manager@example.com", "pass", role=UserRole.MANAGER)
        developer = User.create_user("dev", "dev@example.com", "pass", role=UserRole.DEVELOPER)
        viewer = User.create_user("viewer", "viewer@example.com", "pass", role=UserRole.VIEWER)
        
        assert admin.role == UserRole.ADMIN
        assert manager.role == UserRole.MANAGER
        assert developer.role == UserRole.DEVELOPER
        assert viewer.role == UserRole.VIEWER
    
    def test_permissions(self):
        """Test permission system"""
        user = User.create_user("testuser", "test@example.com", "pass")
        
        # Test basic permissions
        assert user.has_permission(Permission.READ_TASK)
        assert user.has_permission(Permission.CREATE_TASK)
        assert user.has_permission(Permission.UPDATE_TASK)
        
        # Test admin permissions
        admin = User.create_user("admin", "admin@example.com", "pass", role=UserRole.ADMIN)
        assert admin.has_permission(Permission.DELETE_USER)
        assert admin.has_permission(Permission.MANAGE_SYSTEM)
        
        # Test viewer permissions
        viewer = User.create_user("viewer", "viewer@example.com", "pass", role=UserRole.VIEWER)
        assert viewer.has_permission(Permission.READ_TASK)
        assert not viewer.has_permission(Permission.CREATE_TASK)
    
    def test_custom_permissions(self):
        """Test custom permission assignment"""
        user = User.create_user("testuser", "test@example.com", "pass")
        
        # Add custom permission
        user.add_permission(Permission.DELETE_PROJECT)
        assert user.has_permission(Permission.DELETE_PROJECT)
        assert Permission.DELETE_PROJECT in user.custom_permissions
        
        # Remove custom permission
        user.remove_permission(Permission.DELETE_PROJECT)
        assert not user.has_permission(Permission.DELETE_PROJECT)
        assert Permission.DELETE_PROJECT not in user.custom_permissions
    
    def test_team_management(self):
        """Test team membership functionality"""
        user = User.create_user("testuser", "test@example.com", "pass")
        
        # Join teams
        user.join_team("project-123")
        user.join_team("project-456")
        
        assert "project-123" in user.teams
        assert "project-456" in user.teams
        assert len(user.teams) == 2
        
        # Leave team
        user.leave_team("project-123")
        assert "project-123" not in user.teams
        assert "project-456" in user.teams
        assert len(user.teams) == 1
    
    def test_activity_logging(self):
        """Test user activity logging"""
        user = User.create_user("testuser", "test@example.com", "pass")
        
        # Log some activities
        user.log_activity("login", {"ip": "192.168.1.1"})
        user.log_activity("task_created", {"task_id": "task-123"})
        
        assert len(user.activity_log) == 2
        assert user.activity_log[0]["action"] == "login"
        assert user.activity_log[1]["action"] == "task_created"
    
    def test_last_login_update(self):
        """Test last login timestamp update"""
        user = User.create_user("testuser", "test@example.com", "pass")
        
        # Initially no last login
        assert user.last_login is None
        
        # Update last login
        user.update_last_login()
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)
    
    def test_user_deactivation(self):
        """Test user activation/deactivation"""
        user = User.create_user("testuser", "test@example.com", "pass")
        
        # User starts active
        assert user.is_active
        
        # Deactivate user
        user.deactivate()
        assert not user.is_active
        
        # Reactivate user
        user.activate()
        assert user.is_active
    
    def test_user_profile(self):
        """Test user profile functionality"""
        profile_data = {
            "bio": "Software developer with 5 years experience",
            "location": "San Francisco, CA",
            "website": "https://example.com",
            "github": "testuser",
            "linkedin": "test-user"
        }
        
        user = User.create_user("testuser", "test@example.com", "pass")
        user.profile = UserProfile(**profile_data)
        
        assert user.profile.bio == profile_data["bio"]
        assert user.profile.location == profile_data["location"]
        assert user.profile.website == profile_data["website"]
        assert user.profile.social_links["github"] == "testuser"
        assert user.profile.social_links["linkedin"] == "test-user"
    
    def test_user_settings(self):
        """Test user settings management"""
        user = User.create_user("testuser", "test@example.com", "pass")
        
        # Set some settings
        user.update_setting("theme", "dark")
        user.update_setting("notifications.email", True)
        user.update_setting("notifications.push", False)
        
        assert user.get_setting("theme") == "dark"
        assert user.get_setting("notifications.email") is True
        assert user.get_setting("notifications.push") is False
        assert user.get_setting("nonexistent") is None
    
    def test_user_validation(self):
        """Test user validation"""
        # Test invalid email
        with pytest.raises(ValueError):
            User.create_user("testuser", "invalid-email", "pass")
        
        # Test short username
        with pytest.raises(ValueError):
            User.create_user("ab", "test@example.com", "pass")
        
        # Test weak password
        with pytest.raises(ValueError):
            User.create_user("testuser", "test@example.com", "123")
    
    def test_user_serialization(self):
        """Test user serialization"""
        user = User.create_user("testuser", "test@example.com", "pass", full_name="Test User")
        
        # Public dict should not include sensitive data
        public_dict = user.to_public_dict()
        assert "password_hash" not in public_dict
        assert "email" not in public_dict  # Privacy
        assert public_dict["username"] == "testuser"
        assert public_dict["full_name"] == "Test User"
        
        # Full dict includes all fields
        full_dict = user.to_dict()
        assert "password_hash" in full_dict
        assert "email" in full_dict
    
    def test_user_comparison(self):
        """Test user equality comparison"""
        user1 = User.create_user("testuser", "test1@example.com", "pass")
        user2 = User.create_user("testuser2", "test2@example.com", "pass")
        user3 = User(id=user1.id, username="testuser", email="test1@example.com")
        
        # Different users should not be equal
        assert user1 != user2
        
        # Same ID should be equal
        assert user1 == user3
    
    def test_user_string_representation(self):
        """Test user string representations"""
        user = User.create_user("testuser", "test@example.com", "pass", full_name="Test User")
        
        str_repr = str(user)
        assert "testuser" in str_repr
        assert "Test User" in str_repr
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert user.id[:8] in repr_str


class TestUserProfile:
    """Test cases for UserProfile model"""
    
    def test_profile_creation(self):
        """Test user profile creation"""
        profile = UserProfile(
            bio="Software developer",
            location="San Francisco",
            website="https://example.com",
            github="testuser",
            twitter="@testuser"
        )
        
        assert profile.bio == "Software developer"
        assert profile.location == "San Francisco" 
        assert profile.website == "https://example.com"
        assert profile.social_links["github"] == "testuser"
        assert profile.social_links["twitter"] == "@testuser"
    
    def test_avatar_url_generation(self):
        """Test avatar URL generation"""
        profile = UserProfile(
            avatar_url="https://example.com/avatar.jpg"
        )
        
        assert profile.get_avatar_url() == "https://example.com/avatar.jpg"
        
        # Test fallback to gravatar
        user = User.create_user("test", "test@example.com", "pass")
        gravatar_url = user.profile.get_avatar_url("test@example.com")
        assert "gravatar.com" in gravatar_url