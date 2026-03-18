#!/usr/bin/env python3
"""
Generate realistic test data for development
"""

import random
import string
import json
from datetime import datetime, timedelta


class TestDataGenerator:
    """Generate mock test data"""
    
    @staticmethod
    def random_email():
        """Generate random email"""
        name = ''.join(random.choices(string.ascii_lowercase, k=8))
        return f"test_{name}@example.com"
    
    @staticmethod
    def random_password():
        """Generate secure random password"""
        return f"Test{random.randint(100000,999999)}!"
    
    @staticmethod
    def random_store_name():
        """Generate random store name"""
        adjectives = ["Amazing", "Best", "Cool", "Epic", "Fab"]
        nouns = ["Store", "Shop", "Boutique", "Gallery", "Market"]
        return f"{random.choice(adjectives)} {random.choice(nouns)}"
    
    @staticmethod
    def random_shop_domain():
        """Generate random Shopify domain"""
        name = ''.join(random.choices(string.ascii_lowercase, k=6))
        return f"{name}.myshopify.com"
    
    @staticmethod
    def test_user():
        """Generate test user data"""
        return {
            "owner_email": TestDataGenerator.random_email(),
            "password": TestDataGenerator.random_password(),
            "owner_first_name": random.choice(["John", "Jane", "Bob", "Alice"]),
            "owner_last_name": random.choice(["Smith", "Johnson", "Williams", "Brown"])
        }
    
    @staticmethod
    def test_store():
        """Generate test store data"""
        return {
            "store_name": TestDataGenerator.random_store_name(),
            "industry": random.choice(["fashion", "electronics", "food", "beauty", "home"]),
            "target_audience": "Young professionals interested in quality products",
            "monthly_visitors": random.randint(1000, 50000),
            "currency": "USD",
            "timezone": "America/New_York"
        }
    
    @staticmethod
    def test_agents():
        """Generate test agent configuration"""
        return {
            "agents_to_enable": [
                "product_recommender",
                "checkout_assistant",
                "support_bot"
            ],
            "agent_name": random.choice(["Alex", "Jordan", "Sam", "Casey"]),
            "agent_personality": random.choice(["helpful", "friendly", "playful", "professional"])
        }


def main():
    """Generate and print test data"""
    print("Generated Test Data:")
    print("=" * 50)
    
    gen = TestDataGenerator
    
    print("\nUser Data:")
    print(json.dumps(gen.test_user(), indent=2))
    
    print("\nStore Data:")
    print(json.dumps(gen.test_store(), indent=2))
    
    print("\nAgent Data:")
    print(json.dumps(gen.test_agents(), indent=2))


if __name__ == "__main__":
    main()
