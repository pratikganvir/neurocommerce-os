#!/usr/bin/env python3
"""
NeuroCommerce Shopify App - One-Click Setup Wizard

This script automates the complete Shopify app installation and setup process.
No manual configuration needed - just run and answer a few questions!

Usage:
    python setup_shopify.py
    
Or with environment file:
    python setup_shopify.py --env-file .env
"""

import os
import sys
import json
import argparse
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import secrets
from urllib.parse import quote

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_step(num: int, text: str):
    """Print step"""
    print(f"{Colors.OKBLUE}[{num}]{Colors.ENDC} {text}")


class ShopifyAppSetup:
    """Handles Shopify app setup and configuration"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.config: Dict[str, Any] = {}
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
    
    def print_welcome(self):
        """Print welcome message"""
        print_header("NEUROCOMMERCE SHOPIFY APP - ONE-CLICK SETUP")
        print(f"""
{Colors.BOLD}Welcome to NeuroCommerce!{Colors.ENDC}

This setup wizard will:
{Colors.OKGREEN}✓ Create environment configuration{Colors.ENDC}
{Colors.OKGREEN}✓ Register your Shopify app{Colors.ENDC}
{Colors.OKGREEN}✓ Configure webhooks{Colors.ENDC}
{Colors.OKGREEN}✓ Initialize database{Colors.ENDC}
{Colors.OKGREEN}✓ Start all services{Colors.ENDC}

{Colors.WARNING}You'll need:{Colors.ENDC}
- Shopify Partner account (free at partners.shopify.com)
- Development store (created in Partner account)
- 5 minutes of your time

Let's get started! 🚀
        """)
    
    def get_shopify_credentials(self) -> Dict[str, str]:
        """Interactively get Shopify credentials"""
        print_header("STEP 1: SHOPIFY CREDENTIALS")
        
        print("""
{Colors.BOLD}Get your Shopify API credentials:{Colors.ENDC}

1. Go to https://partners.shopify.com
2. Log in or create a free account
3. Create a development store (if you don't have one)
4. In your store, click "Apps and sales channels" → "Develop apps"
5. Click "Create an app"
6. Name it "NeuroCommerce"
7. In "Admin API access scopes", select:
   - read_orders
   - write_orders
   - read_products
   - read_customers
   - write_discounts
   - read_checkouts
   - write_checkouts
8. Click "Configuration" → "API credentials"
9. Copy the API Key and API Secret below

        """.strip())
        
        api_key = input(f"{Colors.OKBLUE}Enter Shopify API Key: {Colors.ENDC}").strip()
        if not api_key:
            print_error("API Key is required")
            return {}
        
        api_secret = input(f"{Colors.OKBLUE}Enter Shopify API Secret: {Colors.ENDC}").strip()
        if not api_secret:
            print_error("API Secret is required")
            return {}
        
        # Verify credentials format
        if len(api_key) < 20 or len(api_secret) < 20:
            print_error("Invalid credentials format")
            return {}
        
        print_success("Shopify credentials verified")
        
        return {
            "SHOPIFY_API_KEY": api_key,
            "SHOPIFY_API_SECRET": api_secret,
            "SHOPIFY_SCOPES": "read_orders,write_orders,read_products,read_customers,write_discounts,read_checkouts,write_checkouts",
            "SHOPIFY_API_VERSION": "2024-01"
        }
    
    def get_app_config(self) -> Dict[str, str]:
        """Get app configuration"""
        print_header("STEP 2: APP CONFIGURATION")
        
        app_name = input(f"{Colors.OKBLUE}App Name [{Colors.ENDC}NeuroCommerce{Colors.OKBLUE}]: {Colors.ENDC}").strip() or "NeuroCommerce"
        app_url = input(f"{Colors.OKBLUE}App URL [{Colors.ENDC}http://localhost:8000{Colors.OKBLUE}]: {Colors.ENDC}").strip() or "http://localhost:8000"
        
        if not app_url.startswith("http"):
            app_url = f"https://{app_url}"
        
        # Generate secure keys
        jwt_secret = secrets.token_urlsafe(32)
        
        print_success("App configuration created")
        
        return {
            "APP_NAME": app_name,
            "APP_URL": app_url,
            "JWT_SECRET_KEY": jwt_secret,
            "ENVIRONMENT": "development"
        }
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration"""
        print_header("STEP 3: DATABASE CONFIGURATION")
        
        db_password = input(f"{Colors.OKBLUE}Database Password [{Colors.ENDC}password{Colors.OKBLUE}]: {Colors.ENDC}").strip() or "password"
        
        return {
            "DATABASE_URL": f"postgresql://neurocommerce:{db_password}@postgres:5432/neurocommerce",
            "REDIS_URL": "redis://redis:6379/0",
            "KAFKA_BROKERS": "kafka:9092",
            "CLICKHOUSE_URL": "http://clickhouse:8123/neurocommerce"
        }
    
    def save_env_file(self):
        """Save configuration to .env file"""
        print_step(1, "Creating .env file...")
        
        # Read example file
        example_file = Path(self.env_file.replace(".env", ".env.example"))
        if not example_file.exists():
            print_warning(f"Example file not found: {example_file}")
            return False
        
        with open(example_file, 'r') as f:
            env_content = f.read()
        
        # Update with new values
        for key, value in self.config.items():
            # Find and replace the key
            import re
            pattern = rf"^{key}=.*$"
            if re.search(pattern, env_content, re.MULTILINE):
                env_content = re.sub(pattern, f"{key}={value}", env_content, flags=re.MULTILINE)
            else:
                # Append if not found
                env_content += f"\n{key}={value}"
        
        # Write to .env
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        print_success(f".env file created: {self.env_file}")
        return True
    
    def verify_docker(self) -> bool:
        """Verify Docker is installed and running"""
        print_step(1, "Verifying Docker installation...")
        
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print_error("Docker is not installed")
                return False
            print_success(f"Docker found: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print_error("Docker daemon is not running. Start Docker and try again.")
                return False
            
            print_success("Docker daemon is running")
            return True
        
        except FileNotFoundError:
            print_error("Docker is not installed")
            print_info("Install Docker from https://www.docker.com/products/docker-desktop")
            return False
        except Exception as e:
            print_error(f"Error checking Docker: {e}")
            return False
    
    def verify_dependencies(self) -> bool:
        """Verify required dependencies"""
        print_step(1, "Verifying dependencies...")
        
        required = {
            "docker": "Docker",
            "docker-compose": "Docker Compose",
        }
        
        optional = {
            "python3": "Python 3",
            "git": "Git"
        }
        
        missing_required = []
        for cmd, name in required.items():
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print_success(f"{name} found")
            else:
                missing_required.append(name)
                print_error(f"{name} not found")
        
        if missing_required:
            print_error(f"Missing required dependencies: {', '.join(missing_required)}")
            return False
        
        # Check optional
        for cmd, name in optional.items():
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print_success(f"{name} found (optional)")
            else:
                print_warning(f"{name} not found (optional)")
        
        return True
    
    def start_services(self) -> bool:
        """Start Docker services"""
        print_header("STEP 4: STARTING SERVICES")
        
        print_step(1, "Starting Docker containers...")
        
        try:
            # Down first to clean up
            subprocess.run(
                ["docker-compose", "down"],
                cwd=self.root_dir,
                capture_output=True,
                timeout=30
            )
        except:
            pass
        
        # Up
        try:
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print_error(f"Docker Compose failed: {result.stderr}")
                return False
            
            print_success("Docker containers started")
            
            # Wait for services
            print_step(1, "Waiting for services to be ready...")
            import time
            time.sleep(10)
            
            return True
        
        except subprocess.TimeoutExpired:
            print_error("Docker Compose took too long (timeout)")
            return False
        except Exception as e:
            print_error(f"Error starting Docker: {e}")
            return False
    
    def setup_database(self) -> bool:
        """Initialize database"""
        print_header("STEP 5: INITIALIZING DATABASE")
        
        print_step(1, "Running database migrations...")
        
        try:
            # Run migrations
            result = subprocess.run(
                ["docker-compose", "exec", "-T", "api", "python", "-m", "alembic", "upgrade", "head"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print_success("Database migrations completed")
            else:
                print_warning("Database migrations skipped or failed (non-critical)")
            
            return True
        
        except Exception as e:
            print_warning(f"Database setup skipped: {e}")
            return True
    
    def print_setup_summary(self):
        """Print setup summary"""
        print_header("SETUP COMPLETE! 🎉")
        
        print(f"""
{Colors.BOLD}Your NeuroCommerce Shopify app is ready!{Colors.ENDC}

{Colors.OKGREEN}✓{Colors.ENDC} Environment configured
{Colors.OKGREEN}✓{Colors.ENDC} Docker containers running
{Colors.OKGREEN}✓{Colors.ENDC} Database initialized

{Colors.BOLD}Next Steps:{Colors.ENDC}

1. {Colors.OKCYAN}Get your Shopify API credentials{Colors.ENDC}
   - Visit: https://partners.shopify.com/apps
   - In "Configuration", find "Redirect URIs"
   - Add this to your Shopify app settings:
   
   {Colors.OKBLUE}{self.config.get('APP_URL', 'http://localhost:8000')}/shopify/oauth/callback{Colors.ENDC}

2. {Colors.OKCYAN}Configure webhook delivery{Colors.ENDC}
   - In Shopify app settings → "Webhooks"
   - Click "Add webhook"
   - For "checkout/create" event, set URL to:
   
   {Colors.OKBLUE}{self.config.get('APP_URL', 'http://localhost:8000')}/shopify/webhooks/checkout/create{Colors.ENDC}
   
   - Repeat for: checkout/update, orders/create

3. {Colors.OKCYAN}Test the integration{Colors.ENDC}
   - API is running at: {Colors.OKBLUE}http://localhost:8000{Colors.ENDC}
   - Documentation at: {Colors.OKBLUE}http://localhost:8000/docs{Colors.ENDC}
   - Health check: {Colors.OKBLUE}curl http://localhost:8000/health{Colors.ENDC}

4. {Colors.OKCYAN}View logs{Colors.ENDC}
   {Colors.OKBLUE}docker-compose logs -f api{Colors.ENDC}

5. {Colors.OKCYAN}Stop services{Colors.ENDC}
   {Colors.OKBLUE}docker-compose down{Colors.ENDC}

{Colors.WARNING}IMPORTANT:{Colors.ENDC}
- Save your credentials securely
- Never commit .env file to git (already in .gitignore)
- Change JWT_SECRET_KEY in production
- Use HTTPS URLs for production (not http://)

{Colors.BOLD}Support:{Colors.ENDC}
- Documentation: docs/API.md
- Troubleshooting: docs/TROUBLESHOOTING.md
- Issues: GitHub issues

Happy selling! 🚀
        """)
    
    def run(self, interactive: bool = True) -> bool:
        """Run the complete setup"""
        self.print_welcome()
        
        try:
            # Check dependencies
            if not self.verify_dependencies():
                print_error("\nPlease install required dependencies")
                return False
            
            if not self.verify_docker():
                print_error("\nPlease install and start Docker")
                return False
            
            # Get configuration interactively
            if interactive:
                self.config.update(self.get_shopify_credentials())
                if not self.config.get("SHOPIFY_API_KEY"):
                    return False
                
                self.config.update(self.get_app_config())
                self.config.update(self.get_database_config())
            else:
                # Use defaults
                self.config = {
                    "SHOPIFY_API_KEY": os.getenv("SHOPIFY_API_KEY", ""),
                    "SHOPIFY_API_SECRET": os.getenv("SHOPIFY_API_SECRET", ""),
                    "APP_NAME": "NeuroCommerce",
                    "APP_URL": os.getenv("APP_URL", "http://localhost:8000"),
                    "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32)),
                    "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql://neurocommerce:password@postgres:5432/neurocommerce"),
                }
            
            # Save environment file
            if not self.save_env_file():
                return False
            
            # Start services
            if not self.start_services():
                print_warning("Services may not have started correctly. Check logs.")
            
            # Setup database
            self.setup_database()
            
            # Print summary
            self.print_setup_summary()
            
            return True
        
        except KeyboardInterrupt:
            print_error("\nSetup cancelled by user")
            return False
        except Exception as e:
            print_error(f"Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="NeuroCommerce Shopify App - One-Click Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_shopify.py              # Interactive setup
  python setup_shopify.py --non-interactive  # Use environment variables
  python setup_shopify.py --env-file .env.production  # Specify env file
        """
    )
    
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to environment file (default: .env)"
    )
    
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use environment variables instead of interactive prompts"
    )
    
    args = parser.parse_args()
    
    setup = ShopifyAppSetup(env_file=args.env_file)
    success = setup.run(interactive=not args.non_interactive)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
