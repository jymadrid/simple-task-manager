#!/usr/bin/env python3
"""
TaskForge Enterprise Integration Examples
========================================

This example demonstrates enterprise-level features including:
- Multi-tenant architecture
- LDAP/SSO integration
- Advanced reporting and analytics
- Compliance and audit logging
- Enterprise-grade deployment patterns

Great for: Enterprise architects, system administrators, IT managers
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from taskforge import TaskManager, Task, Project, TaskPriority, TaskStatus
from taskforge.storage import JsonStorage
from taskforge.core.user import User


class UserRole(Enum):
    """Enterprise user roles."""
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    TEAM_LEAD = "team_lead"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class AuditEventType(Enum):
    """Types of audit events."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    PROJECT_CREATED = "project_created"
    PERMISSIONS_CHANGED = "permissions_changed"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGED = "configuration_changed"


@dataclass
class AuditEvent:
    """Represents an audit log entry."""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: str
    tenant_id: str
    resource_type: str
    resource_id: str
    action: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    session_id: str


@dataclass
class Tenant:
    """Represents a tenant in multi-tenant architecture."""
    id: str
    name: str
    domain: str
    subscription_tier: str  # basic, premium, enterprise
    max_users: int
    max_projects: int
    features_enabled: List[str]
    created_at: datetime
    settings: Dict[str, Any]


@dataclass
class EnterpriseUser:
    """Enterprise user with roles and permissions."""
    id: str
    username: str
    email: str
    tenant_id: str
    role: UserRole
    departments: List[str]
    permissions: List[str]
    ldap_dn: Optional[str]
    last_login: Optional[datetime]
    is_active: bool
    metadata: Dict[str, Any]


class EnterpriseAuditLogger:
    """Enterprise-grade audit logging system."""
    
    def __init__(self):
        self.audit_logs: List[AuditEvent] = []
        self.retention_days = 2555  # 7 years default retention
    
    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        details: Dict[str, Any] = None,
        ip_address: str = "127.0.0.1",
        user_agent: str = "TaskForge-CLI",
        session_id: str = None
    ):
        """Log an audit event."""
        event = AuditEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id or str(uuid.uuid4())
        )
        
        self.audit_logs.append(event)
        print(f"🔍 AUDIT: {event_type.value} by {user_id} on {resource_type}:{resource_id}")
    
    def get_audit_report(
        self,
        tenant_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
        event_types: List[AuditEventType] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Generate audit report for compliance."""
        filtered_logs = self.audit_logs
        
        # Apply filters
        if tenant_id:
            filtered_logs = [log for log in filtered_logs if log.tenant_id == tenant_id]
        
        if start_date:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_date]
        
        if end_date:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_date]
        
        if event_types:
            filtered_logs = [log for log in filtered_logs if log.event_type in event_types]
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        
        # Generate statistics
        event_counts = {}
        user_activity = {}
        
        for log in filtered_logs:
            # Count events by type
            event_type = log.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Track user activity
            if log.user_id not in user_activity:
                user_activity[log.user_id] = {"total_events": 0, "event_types": {}}
            
            user_activity[log.user_id]["total_events"] += 1
            user_activity[log.user_id]["event_types"][event_type] = \
                user_activity[log.user_id]["event_types"].get(event_type, 0) + 1
        
        return {
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "total_events": len(filtered_logs),
            "event_counts": event_counts,
            "user_activity": user_activity,
            "compliance_status": "COMPLIANT",
            "retention_policy_days": self.retention_days
        }


class MultiTenantManager:
    """Multi-tenant management system."""
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.users: Dict[str, EnterpriseUser] = {}
        self.audit_logger = EnterpriseAuditLogger()
    
    async def create_tenant(
        self,
        name: str,
        domain: str,
        subscription_tier: str = "basic",
        admin_user_email: str = None
    ) -> Tenant:
        """Create a new tenant."""
        tenant_id = str(uuid.uuid4())
        
        # Define feature sets by subscription tier
        feature_sets = {
            "basic": ["basic_tasks", "basic_projects", "basic_reports"],
            "premium": ["basic_tasks", "basic_projects", "basic_reports", 
                       "advanced_analytics", "integrations", "custom_fields"],
            "enterprise": ["basic_tasks", "basic_projects", "basic_reports",
                          "advanced_analytics", "integrations", "custom_fields",
                          "sso", "ldap", "audit_logs", "compliance_reports",
                          "custom_branding", "api_access", "white_label"]
        }
        
        # Set limits by subscription tier
        limits = {
            "basic": {"max_users": 10, "max_projects": 50},
            "premium": {"max_users": 100, "max_projects": 500},
            "enterprise": {"max_users": -1, "max_projects": -1}  # Unlimited
        }
        
        tenant = Tenant(
            id=tenant_id,
            name=name,
            domain=domain,
            subscription_tier=subscription_tier,
            max_users=limits[subscription_tier]["max_users"],
            max_projects=limits[subscription_tier]["max_projects"],
            features_enabled=feature_sets[subscription_tier],
            created_at=datetime.now(),
            settings={
                "timezone": "UTC",
                "date_format": "YYYY-MM-DD",
                "working_hours": {"start": "09:00", "end": "17:00"},
                "theme": "default"
            }
        )
        
        self.tenants[tenant_id] = tenant
        
        # Create admin user for tenant
        if admin_user_email:
            await self.create_user(
                username=f"admin_{domain.replace('.', '_')}",
                email=admin_user_email,
                tenant_id=tenant_id,
                role=UserRole.ADMIN
            )
        
        await self.audit_logger.log_event(
            AuditEventType.CONFIGURATION_CHANGED,
            "system",
            tenant_id,
            "tenant",
            tenant_id,
            "create_tenant",
            {"tenant_name": name, "subscription_tier": subscription_tier}
        )
        
        return tenant
    
    async def create_user(
        self,
        username: str,
        email: str,
        tenant_id: str,
        role: UserRole = UserRole.DEVELOPER,
        departments: List[str] = None,
        ldap_dn: str = None
    ) -> EnterpriseUser:
        """Create a new enterprise user."""
        user_id = str(uuid.uuid4())
        
        # Define permissions by role
        role_permissions = {
            UserRole.ADMIN: ["*"],  # All permissions
            UserRole.PROJECT_MANAGER: [
                "project.create", "project.update", "project.delete",
                "task.create", "task.update", "task.assign",
                "user.view", "report.generate"
            ],
            UserRole.TEAM_LEAD: [
                "project.view", "task.create", "task.update", "task.assign",
                "user.view", "report.view"
            ],
            UserRole.DEVELOPER: [
                "task.create", "task.update", "task.view",
                "project.view", "comment.create"
            ],
            UserRole.VIEWER: ["task.view", "project.view", "comment.view"]
        }
        
        user = EnterpriseUser(
            id=user_id,
            username=username,
            email=email,
            tenant_id=tenant_id,
            role=role,
            departments=departments or ["general"],
            permissions=role_permissions[role],
            ldap_dn=ldap_dn,
            last_login=None,
            is_active=True,
            metadata={}
        )
        
        self.users[user_id] = user
        
        await self.audit_logger.log_event(
            AuditEventType.PERMISSIONS_CHANGED,
            "system",
            tenant_id,
            "user",
            user_id,
            "create_user",
            {
                "username": username,
                "role": role.value,
                "departments": departments
            }
        )
        
        return user
    
    def get_tenant_users(self, tenant_id: str) -> List[EnterpriseUser]:
        """Get all users for a tenant."""
        return [user for user in self.users.values() if user.tenant_id == tenant_id]
    
    def check_feature_access(self, tenant_id: str, feature: str) -> bool:
        """Check if tenant has access to a feature."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False
        return feature in tenant.features_enabled
    
    def check_user_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission."""
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False
        
        # Admins have all permissions
        if "*" in user.permissions:
            return True
        
        return permission in user.permissions


class EnterpriseAnalytics:
    """Enterprise analytics and reporting system."""
    
    def __init__(self, tenant_manager: MultiTenantManager):
        self.tenant_manager = tenant_manager
        self.metrics_data = {}
    
    async def generate_executive_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """Generate executive-level dashboard data."""
        tenant = self.tenant_manager.tenants.get(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}
        
        users = self.tenant_manager.get_tenant_users(tenant_id)
        
        # Simulate project and task data
        total_projects = 25
        active_projects = 18
        completed_projects = 7
        
        total_tasks = 847
        completed_tasks = 623
        overdue_tasks = 34
        
        dashboard = {
            "tenant_info": {
                "name": tenant.name,
                "subscription_tier": tenant.subscription_tier,
                "user_count": len(users),
                "max_users": tenant.max_users
            },
            "project_metrics": {
                "total": total_projects,
                "active": active_projects,
                "completed": completed_projects,
                "completion_rate": round((completed_projects / total_projects) * 100, 1)
            },
            "task_metrics": {
                "total": total_tasks,
                "completed": completed_tasks,
                "overdue": overdue_tasks,
                "completion_rate": round((completed_tasks / total_tasks) * 100, 1)
            },
            "team_productivity": {
                "average_tasks_per_user": round(total_tasks / len(users), 1) if users else 0,
                "average_completion_rate": 73.5,
                "top_performers": [
                    {"username": "alice_dev", "completion_rate": 89.2},
                    {"username": "bob_lead", "completion_rate": 87.1},
                    {"username": "charlie_pm", "completion_rate": 82.5}
                ]
            },
            "trends": {
                "weekly_task_creation": [45, 52, 38, 61, 47],
                "weekly_completion": [43, 48, 41, 55, 51],
                "monthly_project_starts": [3, 4, 2, 5, 3, 4]
            },
            "alerts": [
                {"type": "warning", "message": f"{overdue_tasks} tasks are overdue"},
                {"type": "info", "message": "3 projects approaching deadline"},
                {"type": "success", "message": "Team productivity up 12% this month"}
            ]
        }
        
        return dashboard
    
    async def generate_compliance_report(self, tenant_id: str) -> Dict[str, Any]:
        """Generate compliance report for auditing."""
        tenant = self.tenant_manager.tenants.get(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}
        
        # Get audit data for the last 90 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        audit_report = self.tenant_manager.audit_logger.get_audit_report(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        users = self.tenant_manager.get_tenant_users(tenant_id)
        active_users = [u for u in users if u.is_active]
        
        compliance_report = {
            "report_metadata": {
                "tenant_id": tenant_id,
                "tenant_name": tenant.name,
                "report_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "generated_at": datetime.now().isoformat()
            },
            "user_access_control": {
                "total_users": len(users),
                "active_users": len(active_users),
                "inactive_users": len(users) - len(active_users),
                "users_by_role": {
                    role.value: len([u for u in users if u.role == role])
                    for role in UserRole
                },
                "ldap_integrated_users": len([u for u in users if u.ldap_dn])
            },
            "audit_trail": audit_report,
            "data_protection": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "backup_retention_days": 365,
                "data_anonymization": True
            },
            "security_measures": {
                "password_policy_enforced": True,
                "two_factor_authentication": "optional" if tenant.subscription_tier == "basic" else "mandatory",
                "session_timeout_minutes": 60,
                "failed_login_lockout": True
            },
            "compliance_standards": {
                "gdpr_compliant": True,
                "hipaa_compliant": tenant.subscription_tier == "enterprise",
                "soc2_compliant": tenant.subscription_tier in ["premium", "enterprise"],
                "iso27001_aligned": tenant.subscription_tier == "enterprise"
            },
            "recommendations": [
                "Consider enabling mandatory 2FA for all users",
                "Review user access permissions quarterly",
                "Implement automated security scanning",
                "Establish incident response procedures"
            ]
        }
        
        return compliance_report
    
    async def generate_capacity_planning_report(self, tenant_id: str) -> Dict[str, Any]:
        """Generate capacity planning report."""
        tenant = self.tenant_manager.tenants.get(tenant_id)
        users = self.tenant_manager.get_tenant_users(tenant_id)
        
        # Simulate workload data
        current_utilization = {
            "users": len(users) / max(tenant.max_users, 1) * 100 if tenant.max_users > 0 else 0,
            "storage_gb": 15.7,
            "api_calls_per_month": 45000,
            "concurrent_sessions": 8
        }
        
        projected_growth = {
            "user_growth_rate_monthly": 15,  # 15% per month
            "data_growth_rate_monthly": 8,   # 8% per month
            "usage_growth_rate_monthly": 12  # 12% per month
        }
        
        # Calculate projections for next 6 months
        projections = []
        for month in range(1, 7):
            user_projection = len(users) * (1 + projected_growth["user_growth_rate_monthly"] / 100) ** month
            storage_projection = current_utilization["storage_gb"] * (1 + projected_growth["data_growth_rate_monthly"] / 100) ** month
            api_projection = current_utilization["api_calls_per_month"] * (1 + projected_growth["usage_growth_rate_monthly"] / 100) ** month
            
            projections.append({
                "month": month,
                "projected_users": int(user_projection),
                "projected_storage_gb": round(storage_projection, 1),
                "projected_api_calls": int(api_projection)
            })
        
        capacity_report = {
            "current_status": {
                "tenant_tier": tenant.subscription_tier,
                "user_utilization_percent": round(current_utilization["users"], 1),
                "storage_used_gb": current_utilization["storage_gb"],
                "monthly_api_calls": current_utilization["api_calls_per_month"],
                "peak_concurrent_sessions": current_utilization["concurrent_sessions"]
            },
            "projections": projections,
            "recommendations": {
                "upgrade_tier": None,
                "estimated_upgrade_month": None,
                "cost_optimization": [],
                "scaling_actions": []
            }
        }
        
        # Add recommendations based on projections
        if tenant.max_users > 0:  # Not unlimited
            users_in_6_months = projections[-1]["projected_users"]
            if users_in_6_months > tenant.max_users * 0.8:  # 80% utilization threshold
                months_to_limit = next(
                    (p["month"] for p in projections if p["projected_users"] > tenant.max_users),
                    None
                )
                if months_to_limit:
                    capacity_report["recommendations"]["upgrade_tier"] = "premium" if tenant.subscription_tier == "basic" else "enterprise"
                    capacity_report["recommendations"]["estimated_upgrade_month"] = months_to_limit
        
        # Storage and API recommendations
        if projections[-1]["projected_storage_gb"] > 100:
            capacity_report["recommendations"]["scaling_actions"].append("Consider implementing data archiving")
        
        if projections[-1]["projected_api_calls"] > 1000000:
            capacity_report["recommendations"]["scaling_actions"].append("Review API usage patterns for optimization")
        
        return capacity_report


async def enterprise_integration_demo():
    """Demonstrate enterprise integration features."""
    print("🏢 TaskForge Enterprise Integration Demo")
    print("=" * 42)
    
    # Initialize enterprise systems
    tenant_manager = MultiTenantManager()
    analytics = EnterpriseAnalytics(tenant_manager)
    
    print("\n1. Setting up multi-tenant environment...")
    
    # Create enterprise tenant
    enterprise_tenant = await tenant_manager.create_tenant(
        name="Acme Corporation",
        domain="acme.com",
        subscription_tier="enterprise",
        admin_user_email="admin@acme.com"
    )
    
    # Create premium tenant
    premium_tenant = await tenant_manager.create_tenant(
        name="StartupXYZ",
        domain="startupxyz.io",
        subscription_tier="premium",
        admin_user_email="founder@startupxyz.io"
    )
    
    print(f"   ✅ Created enterprise tenant: {enterprise_tenant.name}")
    print(f"   ✅ Created premium tenant: {premium_tenant.name}")
    
    print("\n2. Creating enterprise users...")
    
    # Create users for Acme Corporation
    acme_users = [
        ("john_ceo", "john@acme.com", UserRole.ADMIN, ["executive"]),
        ("sarah_pm", "sarah@acme.com", UserRole.PROJECT_MANAGER, ["engineering", "product"]),
        ("mike_lead", "mike@acme.com", UserRole.TEAM_LEAD, ["engineering"]),
        ("alice_dev", "alice@acme.com", UserRole.DEVELOPER, ["engineering"]),
        ("bob_dev", "bob@acme.com", UserRole.DEVELOPER, ["engineering"]),
        ("lisa_qa", "lisa@acme.com", UserRole.DEVELOPER, ["quality_assurance"]),
    ]
    
    created_acme_users = []
    for username, email, role, departments in acme_users:
        user = await tenant_manager.create_user(
            username=username,
            email=email,
            tenant_id=enterprise_tenant.id,
            role=role,
            departments=departments,
            ldap_dn=f"cn={username},ou=users,dc=acme,dc=com"  # LDAP integration
        )
        created_acme_users.append(user)
        print(f"      👤 Created user: {username} ({role.value}) - {', '.join(departments)}")
    
    # Create users for StartupXYZ
    startup_users = [
        ("founder", "founder@startupxyz.io", UserRole.ADMIN, ["leadership"]),
        ("tech_lead", "tech@startupxyz.io", UserRole.TEAM_LEAD, ["engineering"]),
        ("dev1", "dev1@startupxyz.io", UserRole.DEVELOPER, ["engineering"]),
        ("dev2", "dev2@startupxyz.io", UserRole.DEVELOPER, ["engineering"])
    ]
    
    for username, email, role, departments in startup_users:
        user = await tenant_manager.create_user(
            username=username,
            email=email,
            tenant_id=premium_tenant.id,
            role=role,
            departments=departments
        )
        print(f"      👤 Created startup user: {username} ({role.value})")
    
    print("\n3. Demonstrating role-based access control...")
    
    # Test permission checks
    sarah_pm = created_acme_users[1]  # Project Manager
    alice_dev = created_acme_users[3]  # Developer
    
    permissions_to_test = [
        "project.create",
        "task.assign", 
        "user.view",
        "report.generate"
    ]
    
    for permission in permissions_to_test:
        sarah_can = tenant_manager.check_user_permission(sarah_pm.id, permission)
        alice_can = tenant_manager.check_user_permission(alice_dev.id, permission)
        print(f"      {permission}:")
        print(f"        Sarah (PM): {'✅' if sarah_can else '❌'}")
        print(f"        Alice (Dev): {'✅' if alice_can else '❌'}")
    
    print("\n4. Feature access by subscription tier...")
    
    enterprise_features = ["sso", "ldap", "audit_logs", "compliance_reports"]
    premium_features = ["advanced_analytics", "integrations", "custom_fields"]
    
    print("      Enterprise features (Acme Corp):")
    for feature in enterprise_features:
        has_access = tenant_manager.check_feature_access(enterprise_tenant.id, feature)
        print(f"        {feature}: {'✅' if has_access else '❌'}")
    
    print("      Premium features (StartupXYZ):")
    for feature in enterprise_features:
        has_access = tenant_manager.check_feature_access(premium_tenant.id, feature)
        print(f"        {feature}: {'✅' if has_access else '❌'}")
    
    print("\n5. Audit logging demonstration...")
    
    # Simulate user activities
    audit_logger = tenant_manager.audit_logger
    
    # Simulate login
    await audit_logger.log_event(
        AuditEventType.USER_LOGIN,
        sarah_pm.id,
        enterprise_tenant.id,
        "user",
        sarah_pm.id,
        "login",
        {"login_method": "ldap"},
        "192.168.1.100",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )
    
    # Simulate task creation
    await audit_logger.log_event(
        AuditEventType.TASK_CREATED,
        sarah_pm.id,
        enterprise_tenant.id,
        "task",
        "task_123",
        "create",
        {
            "title": "Implement user authentication",
            "priority": "high",
            "project_id": "proj_456"
        }
    )
    
    # Simulate permission change
    await audit_logger.log_event(
        AuditEventType.PERMISSIONS_CHANGED,
        created_acme_users[0].id,  # Admin
        enterprise_tenant.id,
        "user",
        alice_dev.id,
        "update_permissions",
        {
            "old_role": "developer",
            "new_role": "team_lead",
            "changed_by": created_acme_users[0].username
        }
    )
    
    print(f"      📋 Logged {len(audit_logger.audit_logs)} audit events")
    
    print("\n6. Generating executive dashboard...")
    
    dashboard = await analytics.generate_executive_dashboard(enterprise_tenant.id)
    
    print("      📊 Executive Dashboard (Acme Corp):")
    print(f"        Active Projects: {dashboard['project_metrics']['active']}")
    print(f"        Project Completion Rate: {dashboard['project_metrics']['completion_rate']}%")
    print(f"        Total Tasks: {dashboard['task_metrics']['total']}")
    print(f"        Task Completion Rate: {dashboard['task_metrics']['completion_rate']}%")
    print(f"        Team Size: {dashboard['tenant_info']['user_count']}")
    print(f"        Avg Tasks/User: {dashboard['team_productivity']['average_tasks_per_user']}")
    
    print("      🏆 Top Performers:")
    for performer in dashboard['team_productivity']['top_performers']:
        print(f"        {performer['username']}: {performer['completion_rate']}%")
    
    print("\n7. Compliance reporting...")
    
    compliance_report = await analytics.generate_compliance_report(enterprise_tenant.id)
    
    print("      📋 Compliance Report:")
    print(f"        Total Audit Events: {compliance_report['audit_trail']['total_events']}")
    print(f"        Active Users: {compliance_report['user_access_control']['active_users']}")
    print(f"        LDAP Users: {compliance_report['user_access_control']['ldap_integrated_users']}")
    print(f"        GDPR Compliant: {'✅' if compliance_report['compliance_standards']['gdpr_compliant'] else '❌'}")
    print(f"        SOC2 Compliant: {'✅' if compliance_report['compliance_standards']['soc2_compliant'] else '❌'}")
    print(f"        HIPAA Compliant: {'✅' if compliance_report['compliance_standards']['hipaa_compliant'] else '❌'}")
    
    print("\n8. Capacity planning analysis...")
    
    capacity_report = await analytics.generate_capacity_planning_report(enterprise_tenant.id)
    
    print("      📈 Capacity Planning:")
    print(f"        Current User Utilization: {capacity_report['current_status']['user_utilization_percent']}%")
    print(f"        Storage Used: {capacity_report['current_status']['storage_used_gb']} GB")
    print(f"        Monthly API Calls: {capacity_report['current_status']['monthly_api_calls']:,}")
    
    # Show 6-month projection
    six_month_projection = capacity_report['projections'][-1]
    print(f"        6-Month Projections:")
    print(f"          Users: {six_month_projection['projected_users']}")
    print(f"          Storage: {six_month_projection['projected_storage_gb']} GB")
    print(f"          API Calls: {six_month_projection['projected_api_calls']:,}")
    
    if capacity_report['recommendations']['upgrade_tier']:
        print(f"        💡 Recommendation: Upgrade to {capacity_report['recommendations']['upgrade_tier']} tier")
        print(f"           Estimated upgrade needed in {capacity_report['recommendations']['estimated_upgrade_month']} months")
    
    print("\n9. Enterprise deployment considerations...")
    
    deployment_checklist = [
        "✅ Multi-tenant architecture implemented",
        "✅ Role-based access control (RBAC) configured",
        "✅ LDAP/Active Directory integration ready",
        "✅ Comprehensive audit logging enabled",
        "✅ Compliance reporting automated",
        "✅ Capacity planning metrics collected",
        "✅ Executive dashboards available",
        "⏳ SSO integration pending",
        "⏳ Custom branding configuration needed",
        "⏳ API rate limiting setup required"
    ]
    
    for item in deployment_checklist:
        print(f"      {item}")
    
    print("\n✨ Enterprise integration demo completed!")
    
    return {
        "tenant_manager": tenant_manager,
        "analytics": analytics,
        "tenants": [enterprise_tenant, premium_tenant],
        "users": created_acme_users,
        "dashboard": dashboard,
        "compliance_report": compliance_report,
        "capacity_report": capacity_report
    }


async def main():
    """Run enterprise integration examples."""
    print("🏢 TaskForge Enterprise Integration Examples")
    print("=" * 50)
    print("This demo showcases:")
    print("- Multi-tenant SaaS architecture")
    print("- Enterprise authentication and authorization")
    print("- Comprehensive audit logging")
    print("- Executive dashboards and analytics")
    print("- Compliance reporting")
    print("- Capacity planning and scaling")
    print("=" * 50)
    
    try:
        results = await enterprise_integration_demo()
        
        print("\n\n🎉 Enterprise Integration Demo Completed!")
        print("=" * 47)
        print(f"✅ Tenants created: {len(results['tenants'])}")
        print(f"👥 Enterprise users: {len(results['users'])}")
        print(f"🔍 Audit events logged: {len(results['tenant_manager'].audit_logger.audit_logs)}")
        print(f"📊 Analytics reports generated: 3")
        
        print("\n🏢 Enterprise Readiness Checklist:")
        print("- ✅ Multi-tenancy support")
        print("- ✅ Role-based permissions")
        print("- ✅ Audit trail compliance")
        print("- ✅ Executive reporting")
        print("- ✅ Capacity planning")
        print("- ✅ Security standards adherence")
        
        print("\n🔗 Enterprise Resources:")
        print("- Enterprise Documentation: https://docs.taskforge.dev/enterprise")
        print("- Deployment Guides: https://docs.taskforge.dev/deployment")
        print("- Security Whitepaper: https://docs.taskforge.dev/security")
        print("- Enterprise Support: enterprise@taskforge.dev")
        
    except Exception as e:
        print(f"\n❌ Error in enterprise integration demo: {e}")
        print("Please check your TaskForge installation and enterprise dependencies.")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())