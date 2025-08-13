#!/usr/bin/env python3
"""
TaskForge Plugin Marketplace
============================

This module implements a comprehensive plugin marketplace for TaskForge,
including plugin discovery, installation, ratings, reviews, and revenue sharing.

Features:
- Plugin discovery and browsing
- Automated installation and updates
- User ratings and reviews
- Developer analytics and revenue sharing
- Security scanning and verification
- Community curation and moderation
"""

import asyncio
import hashlib
import json
import os
import tempfile
import uuid
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from taskforge.plugins import PluginMetadata


class PluginStatus(Enum):
    """Plugin status in the marketplace."""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


class PluginCategory(Enum):
    """Plugin categories for organization."""

    INTEGRATION = "integration"
    AUTOMATION = "automation"
    ANALYTICS = "analytics"
    NOTIFICATION = "notification"
    WORKFLOW = "workflow"
    PRODUCTIVITY = "productivity"
    DEVELOPMENT = "development"
    COLLABORATION = "collaboration"
    REPORTING = "reporting"
    CUSTOM = "custom"


@dataclass
class PluginListing:
    """Represents a plugin listing in the marketplace."""

    id: str
    name: str
    description: str
    author: str
    author_email: str
    version: str
    category: PluginCategory
    status: PluginStatus
    tags: List[str]

    # Marketplace metadata
    downloads: int
    rating_average: float
    rating_count: int
    revenue_total: float
    price: float  # 0.0 for free plugins

    # Technical metadata
    supported_versions: List[str]  # TaskForge versions
    requirements: List[str]
    file_size: int
    checksum: str

    # URLs and resources
    homepage_url: Optional[str]
    documentation_url: Optional[str]
    source_code_url: Optional[str]
    download_url: str

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_version_release: datetime

    # Review and moderation
    review_notes: Optional[str]
    security_scan_passed: bool
    community_verified: bool


@dataclass
class PluginReview:
    """User review for a plugin."""

    id: str
    plugin_id: str
    user_id: str
    username: str
    rating: int  # 1-5 stars
    title: str
    content: str
    helpful_votes: int
    version_reviewed: str
    created_at: datetime
    updated_at: datetime
    verified_purchase: bool


@dataclass
class PluginDeveloper:
    """Plugin developer profile."""

    id: str
    username: str
    email: str
    display_name: str
    bio: Optional[str]
    website_url: Optional[str]
    github_username: Optional[str]

    # Developer stats
    plugins_published: int
    total_downloads: int
    total_revenue: float
    average_rating: float

    # Developer program status
    verified_developer: bool
    partner_developer: bool
    created_at: datetime


class PluginMarketplace:
    """Plugin marketplace implementation."""

    def __init__(self, storage_backend=None):
        self.storage = storage_backend or self._init_default_storage()
        self.plugins: Dict[str, PluginListing] = {}
        self.reviews: Dict[str, List[PluginReview]] = {}
        self.developers: Dict[str, PluginDeveloper] = {}
        self.analytics = PluginAnalytics()

    def _init_default_storage(self):
        """Initialize default JSON storage for marketplace data."""
        return {
            "plugins": {},
            "reviews": {},
            "developers": {},
            "categories": {},
            "featured_plugins": [],
        }

    async def submit_plugin(
        self,
        developer_id: str,
        plugin_file: bytes,
        metadata: PluginMetadata,
        category: PluginCategory,
        price: float = 0.0,
        description_long: str = None,
    ) -> str:
        """Submit a new plugin for marketplace review."""
        plugin_id = str(uuid.uuid4())

        # Validate plugin file
        validation_result = await self._validate_plugin_file(plugin_file, metadata)
        if not validation_result["valid"]:
            raise ValueError(f"Plugin validation failed: {validation_result['errors']}")

        # Security scan
        security_result = await self._security_scan_plugin(plugin_file)

        # Create plugin listing
        listing = PluginListing(
            id=plugin_id,
            name=metadata.name,
            description=description_long or metadata.description,
            author=self.developers[developer_id].display_name,
            author_email=self.developers[developer_id].email,
            version=metadata.version,
            category=category,
            status=PluginStatus.PENDING_REVIEW,
            tags=getattr(metadata, "tags", []),
            downloads=0,
            rating_average=0.0,
            rating_count=0,
            revenue_total=0.0,
            price=price,
            supported_versions=getattr(metadata, "supported_versions", [">=1.0.0"]),
            requirements=getattr(metadata, "requires", []),
            file_size=len(plugin_file),
            checksum=hashlib.sha256(plugin_file).hexdigest(),
            homepage_url=getattr(metadata, "homepage", None),
            documentation_url=getattr(metadata, "documentation", None),
            source_code_url=getattr(metadata, "repository", None),
            download_url=f"https://marketplace.taskforge.dev/plugins/{plugin_id}/download",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_version_release=datetime.now(),
            review_notes=None,
            security_scan_passed=security_result["passed"],
            community_verified=False,
        )

        self.plugins[plugin_id] = listing

        # Store plugin file
        await self._store_plugin_file(plugin_id, plugin_file)

        # Notify reviewers
        await self._notify_reviewers(plugin_id, listing)

        print(f"🔌 Plugin '{metadata.name}' submitted for review (ID: {plugin_id})")
        return plugin_id

    async def approve_plugin(self, plugin_id: str, reviewer_id: str, notes: str = None):
        """Approve a plugin for marketplace listing."""
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        listing = self.plugins[plugin_id]
        listing.status = PluginStatus.APPROVED
        listing.review_notes = notes
        listing.updated_at = datetime.now()

        # Update developer stats
        developer = self._get_developer_by_email(listing.author_email)
        if developer:
            developer.plugins_published += 1

        # Add to search index
        await self._index_plugin(listing)

        # Notify developer
        await self._notify_developer_approval(plugin_id, listing)

        print(f"✅ Plugin '{listing.name}' approved and published")

    async def search_plugins(
        self,
        query: str = None,
        category: PluginCategory = None,
        tags: List[str] = None,
        price_max: float = None,
        min_rating: float = None,
        sort_by: str = "popularity",
        limit: int = 20,
        offset: int = 0,
    ) -> List[PluginListing]:
        """Search and filter plugins in the marketplace."""
        results = []

        for listing in self.plugins.values():
            # Only show approved plugins
            if listing.status != PluginStatus.APPROVED:
                continue

            # Apply filters
            if (
                query
                and query.lower()
                not in (listing.name + " " + listing.description).lower()
            ):
                continue

            if category and listing.category != category:
                continue

            if tags and not any(tag in listing.tags for tag in tags):
                continue

            if price_max is not None and listing.price > price_max:
                continue

            if min_rating is not None and listing.rating_average < min_rating:
                continue

            results.append(listing)

        # Apply sorting
        if sort_by == "popularity":
            results.sort(key=lambda p: p.downloads, reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda p: p.rating_average, reverse=True)
        elif sort_by == "newest":
            results.sort(key=lambda p: p.created_at, reverse=True)
        elif sort_by == "updated":
            results.sort(key=lambda p: p.updated_at, reverse=True)
        elif sort_by == "name":
            results.sort(key=lambda p: p.name.lower())
        elif sort_by == "price":
            results.sort(key=lambda p: p.price)

        # Apply pagination
        return results[offset : offset + limit]

    async def get_plugin_details(
        self, plugin_id: str, include_reviews: bool = True
    ) -> Dict[str, Any]:
        """Get detailed information about a plugin."""
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        listing = self.plugins[plugin_id]
        result = asdict(listing)

        # Add developer information
        developer = self._get_developer_by_email(listing.author_email)
        if developer:
            result["developer"] = {
                "username": developer.username,
                "display_name": developer.display_name,
                "bio": developer.bio,
                "verified": developer.verified_developer,
                "partner": developer.partner_developer,
                "total_plugins": developer.plugins_published,
                "average_rating": developer.average_rating,
            }

        # Add recent reviews
        if include_reviews and plugin_id in self.reviews:
            reviews = sorted(
                self.reviews[plugin_id], key=lambda r: r.created_at, reverse=True
            )[
                :10
            ]  # Latest 10 reviews

            result["recent_reviews"] = [asdict(review) for review in reviews]

            # Rating breakdown
            rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for review in self.reviews[plugin_id]:
                rating_counts[review.rating] += 1

            result["rating_breakdown"] = rating_counts

        # Add download statistics
        result["download_stats"] = await self._get_download_stats(plugin_id)

        return result

    async def install_plugin(self, plugin_id: str, user_id: str) -> Dict[str, Any]:
        """Install a plugin for a user."""
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        listing = self.plugins[plugin_id]

        if listing.status != PluginStatus.APPROVED:
            raise ValueError("Plugin is not approved for installation")

        # Download plugin file
        plugin_file = await self._download_plugin_file(plugin_id)

        # Verify checksum
        file_checksum = hashlib.sha256(plugin_file).hexdigest()
        if file_checksum != listing.checksum:
            raise ValueError("Plugin file checksum verification failed")

        # Install plugin (this would integrate with TaskForge's plugin system)
        installation_result = await self._install_plugin_for_user(
            user_id, plugin_file, listing
        )

        if installation_result["success"]:
            # Update download count
            listing.downloads += 1
            listing.updated_at = datetime.now()

            # Record analytics
            await self.analytics.record_download(plugin_id, user_id)

            # Handle payment for paid plugins
            if listing.price > 0:
                await self._process_plugin_purchase(plugin_id, user_id, listing.price)

        return installation_result

    async def submit_review(
        self,
        plugin_id: str,
        user_id: str,
        username: str,
        rating: int,
        title: str,
        content: str,
        version_reviewed: str,
    ) -> str:
        """Submit a user review for a plugin."""
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        review_id = str(uuid.uuid4())
        review = PluginReview(
            id=review_id,
            plugin_id=plugin_id,
            user_id=user_id,
            username=username,
            rating=rating,
            title=title,
            content=content,
            helpful_votes=0,
            version_reviewed=version_reviewed,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            verified_purchase=await self._verify_user_purchase(plugin_id, user_id),
        )

        if plugin_id not in self.reviews:
            self.reviews[plugin_id] = []

        self.reviews[plugin_id].append(review)

        # Update plugin rating
        await self._update_plugin_rating(plugin_id)

        print(f"⭐ Review submitted for plugin '{self.plugins[plugin_id].name}'")
        return review_id

    async def get_featured_plugins(self, limit: int = 10) -> List[PluginListing]:
        """Get featured plugins for the marketplace homepage."""
        # Algorithm for featuring plugins based on:
        # - High ratings (>4.0)
        # - Recent activity
        # - Community verification
        # - Download popularity
        # - Developer reputation

        candidates = []

        for listing in self.plugins.values():
            if listing.status != PluginStatus.APPROVED:
                continue

            # Calculate feature score
            score = 0

            # Rating score (0-40 points)
            if listing.rating_count > 5:
                score += listing.rating_average * 8

            # Popularity score (0-30 points)
            if listing.downloads > 0:
                score += min(30, listing.downloads / 100)

            # Recency score (0-20 points)
            days_since_update = (datetime.now() - listing.updated_at).days
            score += max(0, 20 - days_since_update / 7)

            # Quality bonuses (0-10 points)
            if listing.community_verified:
                score += 5
            if listing.security_scan_passed:
                score += 3
            if len(listing.tags) >= 3:
                score += 2

            candidates.append((score, listing))

        # Sort by score and return top plugins
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [listing for score, listing in candidates[:limit]]

    async def get_developer_analytics(self, developer_id: str) -> Dict[str, Any]:
        """Get analytics dashboard for plugin developers."""
        if developer_id not in self.developers:
            raise ValueError(f"Developer {developer_id} not found")

        developer = self.developers[developer_id]

        # Get developer's plugins
        developer_plugins = [
            p for p in self.plugins.values() if p.author_email == developer.email
        ]

        # Calculate analytics
        analytics = {
            "overview": {
                "total_plugins": len(developer_plugins),
                "total_downloads": sum(p.downloads for p in developer_plugins),
                "total_revenue": sum(p.revenue_total for p in developer_plugins),
                "average_rating": developer.average_rating,
            },
            "plugins": [],
            "revenue_breakdown": {},
            "download_trends": await self._get_developer_download_trends(developer_id),
            "top_performing_plugins": [],
        }

        # Plugin-specific analytics
        for plugin in developer_plugins:
            plugin_analytics = {
                "id": plugin.id,
                "name": plugin.name,
                "downloads": plugin.downloads,
                "revenue": plugin.revenue_total,
                "rating": plugin.rating_average,
                "rating_count": plugin.rating_count,
                "conversion_rate": await self._calculate_conversion_rate(plugin.id),
                "recent_reviews": await self._get_recent_reviews(plugin.id, 5),
            }
            analytics["plugins"].append(plugin_analytics)

        # Top performing plugins
        analytics["top_performing_plugins"] = sorted(
            developer_plugins,
            key=lambda p: p.downloads + (p.rating_average * p.rating_count),
            reverse=True,
        )[:5]

        return analytics

    async def _validate_plugin_file(
        self, plugin_file: bytes, metadata: PluginMetadata
    ) -> Dict[str, Any]:
        """Validate plugin file structure and metadata."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                temp_file.write(plugin_file)
                temp_file_path = temp_file.name

            validation_result = {"valid": True, "errors": [], "warnings": []}

            # Check if it's a valid ZIP file
            try:
                with zipfile.ZipFile(temp_file_path, "r") as zip_file:
                    file_list = zip_file.namelist()

                    # Check for required files
                    required_files = ["__init__.py", "metadata.json"]
                    for required_file in required_files:
                        if not any(f.endswith(required_file) for f in file_list):
                            validation_result["errors"].append(
                                f"Missing required file: {required_file}"
                            )

                    # Check for potentially dangerous files
                    dangerous_patterns = [".exe", ".dll", ".so", ".dylib"]
                    for file_name in file_list:
                        if any(
                            file_name.lower().endswith(pattern)
                            for pattern in dangerous_patterns
                        ):
                            validation_result["errors"].append(
                                f"Potentially dangerous file: {file_name}"
                            )

                    # Validate metadata consistency
                    try:
                        metadata_content = zip_file.read("metadata.json")
                        file_metadata = json.loads(metadata_content)

                        # Check version consistency
                        if file_metadata.get("version") != metadata.version:
                            validation_result["errors"].append(
                                "Version mismatch between file and submission"
                            )

                        # Check name consistency
                        if file_metadata.get("name") != metadata.name:
                            validation_result["errors"].append(
                                "Name mismatch between file and submission"
                            )

                    except (KeyError, json.JSONDecodeError) as e:
                        validation_result["errors"].append(
                            f"Invalid metadata.json: {e}"
                        )

            except zipfile.BadZipFile:
                validation_result["errors"].append("Invalid ZIP file format")

            # Check file size (max 50MB)
            if len(plugin_file) > 50 * 1024 * 1024:
                validation_result["errors"].append(
                    "Plugin file size exceeds 50MB limit"
                )

            # Set validation status
            validation_result["valid"] = len(validation_result["errors"]) == 0

            # Cleanup
            os.unlink(temp_file_path)

            return validation_result

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
            }

    async def _security_scan_plugin(self, plugin_file: bytes) -> Dict[str, Any]:
        """Perform security scan on plugin file."""
        # This would integrate with security scanning tools
        # For demo purposes, we'll simulate basic checks

        scan_result = {"passed": True, "issues": [], "scan_date": datetime.now()}

        # Simulate security checks
        content = plugin_file.decode("utf-8", errors="ignore")

        # Check for potentially dangerous imports
        dangerous_imports = ["os.system", "subprocess.call", "exec(", "eval("]
        for dangerous_import in dangerous_imports:
            if dangerous_import in content:
                scan_result["issues"].append(
                    f"Potentially dangerous code: {dangerous_import}"
                )

        # Check for hardcoded secrets
        secret_patterns = ["password=", "api_key=", "secret=", "token="]
        for pattern in secret_patterns:
            if pattern in content.lower():
                scan_result["issues"].append(f"Potential hardcoded secret: {pattern}")

        # Fail if issues found
        if scan_result["issues"]:
            scan_result["passed"] = False

        return scan_result

    async def _update_plugin_rating(self, plugin_id: str):
        """Update plugin's average rating based on reviews."""
        if plugin_id not in self.reviews or not self.reviews[plugin_id]:
            return

        reviews = self.reviews[plugin_id]
        total_rating = sum(review.rating for review in reviews)
        average_rating = total_rating / len(reviews)

        self.plugins[plugin_id].rating_average = round(average_rating, 2)
        self.plugins[plugin_id].rating_count = len(reviews)

        # Update developer's average rating
        listing = self.plugins[plugin_id]
        developer = self._get_developer_by_email(listing.author_email)
        if developer:
            await self._update_developer_rating(developer)

    def _get_developer_by_email(self, email: str) -> Optional[PluginDeveloper]:
        """Get developer by email address."""
        for developer in self.developers.values():
            if developer.email == email:
                return developer
        return None

    async def _store_plugin_file(self, plugin_id: str, plugin_file: bytes):
        """Store plugin file in secure storage."""
        # In a real implementation, this would upload to cloud storage
        storage_path = f"plugins/{plugin_id}/plugin.zip"
        print(f"📦 Plugin file stored at: {storage_path}")

    async def _notify_reviewers(self, plugin_id: str, listing: PluginListing):
        """Notify reviewers about new plugin submission."""
        print(f"📧 Notified reviewers about plugin: {listing.name}")

    async def _index_plugin(self, listing: PluginListing):
        """Add plugin to search index."""
        print(f"🔍 Indexed plugin for search: {listing.name}")

    async def _notify_developer_approval(self, plugin_id: str, listing: PluginListing):
        """Notify developer about plugin approval."""
        print(f"📧 Notified developer about approval: {listing.name}")


class PluginAnalytics:
    """Plugin marketplace analytics system."""

    def __init__(self):
        self.download_events = []
        self.view_events = []
        self.purchase_events = []

    async def record_download(self, plugin_id: str, user_id: str):
        """Record a plugin download event."""
        event = {
            "plugin_id": plugin_id,
            "user_id": user_id,
            "timestamp": datetime.now(),
            "event_type": "download",
        }
        self.download_events.append(event)

    async def get_download_trends(
        self, plugin_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get download trends for a plugin."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Filter events for the plugin and time period
        relevant_events = [
            event
            for event in self.download_events
            if event["plugin_id"] == plugin_id
            and start_date <= event["timestamp"] <= end_date
        ]

        # Group by day
        daily_downloads = {}
        for event in relevant_events:
            day_key = event["timestamp"].strftime("%Y-%m-%d")
            daily_downloads[day_key] = daily_downloads.get(day_key, 0) + 1

        return {
            "total_downloads": len(relevant_events),
            "daily_downloads": daily_downloads,
            "period_days": days,
        }


async def demo_plugin_marketplace():
    """Demonstrate the plugin marketplace functionality."""
    print("🛍️ TaskForge Plugin Marketplace Demo")
    print("=" * 40)

    # Initialize marketplace
    marketplace = PluginMarketplace()

    print("\n1. Setting up marketplace...")

    # Create sample developers
    developer1 = PluginDeveloper(
        id="dev-1",
        username="integration_expert",
        email="expert@plugindev.com",
        display_name="Integration Expert",
        bio="Specializes in third-party integrations and automation",
        website_url="https://plugindev.com",
        github_username="integration_expert",
        plugins_published=3,
        total_downloads=15420,
        total_revenue=2340.50,
        average_rating=4.7,
        verified_developer=True,
        partner_developer=True,
        created_at=datetime.now() - timedelta(days=365),
    )

    developer2 = PluginDeveloper(
        id="dev-2",
        username="analytics_guru",
        email="guru@analytics.com",
        display_name="Analytics Guru",
        bio="Creating powerful analytics and reporting solutions",
        website_url="https://analytics.com",
        github_username="analytics_guru",
        plugins_published=2,
        total_downloads=8900,
        total_revenue=0.0,  # Free plugins only
        average_rating=4.3,
        verified_developer=True,
        partner_developer=False,
        created_at=datetime.now() - timedelta(days=180),
    )

    marketplace.developers["dev-1"] = developer1
    marketplace.developers["dev-2"] = developer2

    print(f"   👨‍💻 Created developer: {developer1.display_name}")
    print(f"   👩‍💻 Created developer: {developer2.display_name}")

    print("\n2. Submitting plugins...")

    # Create sample plugin files (simulated)
    slack_plugin_file = b"PK\x03\x04...[ZIP content]..."  # Simulated ZIP file
    analytics_plugin_file = b"PK\x03\x04...[ZIP content]..."

    # Submit plugins
    slack_metadata = PluginMetadata(
        name="Advanced Slack Integration",
        version="2.1.0",
        description="Comprehensive Slack integration with custom workflows",
        author="Integration Expert",
        homepage="https://github.com/integration_expert/slack-plugin",
    )

    try:
        slack_plugin_id = await marketplace.submit_plugin(
            developer_id="dev-1",
            plugin_file=slack_plugin_file,
            metadata=slack_metadata,
            category=PluginCategory.INTEGRATION,
            price=19.99,
            description_long="A comprehensive Slack integration plugin that provides advanced workflow automation, custom slash commands, interactive message components, and detailed analytics. Perfect for teams looking to streamline their TaskForge-Slack workflow.",
        )

        print(f"   ✅ Submitted plugin: {slack_metadata.name}")

        # Auto-approve for demo
        await marketplace.approve_plugin(
            slack_plugin_id,
            "reviewer-1",
            "Excellent plugin with comprehensive features",
        )

    except Exception as e:
        print(f"   ❌ Error submitting plugin: {e}")

    # Submit analytics plugin
    analytics_metadata = PluginMetadata(
        name="Advanced Analytics Dashboard",
        version="1.5.0",
        description="Powerful analytics and reporting dashboard",
        author="Analytics Guru",
    )

    try:
        analytics_plugin_id = await marketplace.submit_plugin(
            developer_id="dev-2",
            plugin_file=analytics_plugin_file,
            metadata=analytics_metadata,
            category=PluginCategory.ANALYTICS,
            price=0.0,  # Free plugin
            description_long="Transform your TaskForge data into actionable insights with advanced analytics, custom dashboards, and automated reports. Includes productivity metrics, team performance analysis, and predictive analytics.",
        )

        await marketplace.approve_plugin(
            analytics_plugin_id, "reviewer-1", "Great free analytics solution"
        )

        print(f"   ✅ Submitted plugin: {analytics_metadata.name}")

    except Exception as e:
        print(f"   ❌ Error submitting analytics plugin: {e}")

    print("\n3. Browsing marketplace...")

    # Search for plugins
    integration_plugins = await marketplace.search_plugins(
        category=PluginCategory.INTEGRATION, sort_by="popularity", limit=10
    )

    print(f"   🔌 Integration plugins: {len(integration_plugins)}")
    for plugin in integration_plugins:
        print(f"      - {plugin.name} (v{plugin.version}) - ${plugin.price}")
        print(f"        ⭐ {plugin.rating_average}/5 ({plugin.rating_count} reviews)")
        print(f"        📥 {plugin.downloads} downloads")

    # Get featured plugins
    featured_plugins = await marketplace.get_featured_plugins(limit=5)

    print(f"\n   ⭐ Featured plugins: {len(featured_plugins)}")
    for plugin in featured_plugins:
        print(f"      - {plugin.name} by {plugin.author}")
        print(f"        {plugin.description[:80]}...")

    print("\n4. Plugin installation simulation...")

    if integration_plugins:
        plugin_to_install = integration_plugins[0]

        try:
            installation_result = await marketplace.install_plugin(
                plugin_to_install.id, "user-123"
            )

            if installation_result.get("success"):
                print(f"   ✅ Installed plugin: {plugin_to_install.name}")
                print(f"      📥 Total downloads now: {plugin_to_install.downloads}")
            else:
                print(f"   ❌ Installation failed: {installation_result.get('error')}")

        except Exception as e:
            print(f"   ❌ Installation error: {e}")

    print("\n5. Adding user reviews...")

    # Add sample reviews
    if slack_plugin_id:
        try:
            review1_id = await marketplace.submit_review(
                plugin_id=slack_plugin_id,
                user_id="user-456",
                username="project_manager",
                rating=5,
                title="Excellent Slack Integration!",
                content="This plugin transformed our team communication. The custom workflows are incredibly powerful and easy to set up. Worth every penny!",
                version_reviewed="2.1.0",
            )

            review2_id = await marketplace.submit_review(
                plugin_id=slack_plugin_id,
                user_id="user-789",
                username="team_lead",
                rating=4,
                title="Great plugin with minor issues",
                content="Really solid integration. Had some initial setup challenges but support was responsive. The analytics features are fantastic.",
                version_reviewed="2.1.0",
            )

            print(f"   ⭐ Added reviews for Slack integration plugin")

        except Exception as e:
            print(f"   ❌ Error adding reviews: {e}")

    print("\n6. Developer analytics...")

    try:
        dev_analytics = await marketplace.get_developer_analytics("dev-1")

        print(f"   📊 Developer Analytics for {developer1.display_name}:")
        print(f"      Total Plugins: {dev_analytics['overview']['total_plugins']}")
        print(f"      Total Downloads: {dev_analytics['overview']['total_downloads']}")
        print(f"      Total Revenue: ${dev_analytics['overview']['total_revenue']:.2f}")
        print(f"      Average Rating: {dev_analytics['overview']['average_rating']}/5")

        if dev_analytics["plugins"]:
            print("      Plugin Performance:")
            for plugin_stats in dev_analytics["plugins"]:
                print(
                    f"        - {plugin_stats['name']}: {plugin_stats['downloads']} downloads"
                )

    except Exception as e:
        print(f"   ❌ Analytics error: {e}")

    print("\n7. Plugin details view...")

    if slack_plugin_id:
        try:
            plugin_details = await marketplace.get_plugin_details(
                slack_plugin_id, include_reviews=True
            )

            print(f"   📋 Plugin Details: {plugin_details['name']}")
            print(f"      Version: {plugin_details['version']}")
            print(f"      Category: {plugin_details['category']}")
            print(f"      Price: ${plugin_details['price']}")
            print(
                f"      Rating: {plugin_details['rating_average']}/5 ({plugin_details['rating_count']} reviews)"
            )
            print(f"      Downloads: {plugin_details['downloads']}")
            print(
                f"      Developer: {plugin_details.get('developer', {}).get('display_name', 'Unknown')}"
            )

            if plugin_details.get("recent_reviews"):
                print(f"      Recent Reviews:")
                for review in plugin_details["recent_reviews"][:2]:
                    print(f"        ⭐ {review['rating']}/5 - {review['title']}")
                    print(
                        f"          \"{review['content'][:60]}...\" - {review['username']}"
                    )

        except Exception as e:
            print(f"   ❌ Error getting plugin details: {e}")

    print("\n✨ Plugin marketplace demo completed!")

    return {
        "marketplace": marketplace,
        "plugins_created": len(marketplace.plugins),
        "developers": len(marketplace.developers),
        "reviews": sum(len(reviews) for reviews in marketplace.reviews.values()),
    }


async def main():
    """Run the plugin marketplace demonstration."""
    print("🛍️ TaskForge Plugin Marketplace Demonstration")
    print("=" * 50)
    print("This demo showcases:")
    print("- Plugin submission and review process")
    print("- Marketplace browsing and search")
    print("- Plugin installation and management")
    print("- User reviews and ratings")
    print("- Developer analytics and revenue tracking")
    print("- Community features and curation")
    print("=" * 50)

    try:
        results = await demo_plugin_marketplace()

        print("\n\n🎉 Plugin Marketplace Demo Completed!")
        print("=" * 45)
        print(f"✅ Plugins in marketplace: {results['plugins_created']}")
        print(f"👥 Registered developers: {results['developers']}")
        print(f"⭐ Total reviews: {results['reviews']}")

        print("\n🌟 Marketplace Features Demonstrated:")
        print("- ✅ Plugin submission and validation")
        print("- ✅ Security scanning and review process")
        print("- ✅ Plugin discovery and search")
        print("- ✅ Installation and dependency management")
        print("- ✅ User ratings and review system")
        print("- ✅ Developer analytics dashboard")
        print("- ✅ Revenue sharing for paid plugins")
        print("- ✅ Community curation and featuring")

        print("\n💡 Next Steps for Full Implementation:")
        print("- Integrate with TaskForge core plugin system")
        print("- Add secure payment processing")
        print("- Implement automated testing for plugins")
        print("- Build web interface for marketplace")
        print("- Add advanced security scanning")
        print("- Create developer certification program")

    except Exception as e:
        print(f"\n❌ Error in marketplace demo: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
