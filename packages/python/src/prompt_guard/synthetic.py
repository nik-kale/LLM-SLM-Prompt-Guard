"""
Synthetic data generation for testing PII detection and anonymization.

This module provides utilities for generating realistic fake PII data
for testing, development, and demonstration purposes.

Example:
    >>> from prompt_guard.synthetic import SyntheticDataGenerator
    >>> gen = SyntheticDataGenerator()
    >>> data = gen.generate_pii("EMAIL", count=5)
    >>> print(data)
    ['john.doe@example.com', 'jane.smith@test.org', ...]
"""

import random
import string
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta


class SyntheticDataGenerator:
    """
    Generate realistic synthetic PII data for testing.

    This class provides methods to generate various types of PII including
    names, emails, phone numbers, addresses, SSNs, credit cards, and more.

    Example:
        >>> gen = SyntheticDataGenerator(seed=42)  # Reproducible
        >>> emails = gen.generate_pii("EMAIL", count=10)
        >>> text = gen.generate_text_with_pii(
        ...     template="Contact {NAME} at {EMAIL} or {PHONE}",
        ...     count=5
        ... )
    """

    # Name components
    FIRST_NAMES = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
        "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
        "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
        "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
        "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
        "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    ]

    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
        "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
        "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
        "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
        "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
        "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    ]

    # Email domains
    EMAIL_DOMAINS = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "example.com",
        "test.com", "mail.com", "email.com", "inbox.com", "company.com",
        "corporation.org", "business.net", "enterprise.com", "startup.io",
    ]

    # Street names
    STREET_NAMES = [
        "Main", "Oak", "Maple", "Park", "Elm", "Washington", "Lake", "Hill",
        "Cedar", "Pine", "First", "Second", "Third", "Fourth", "Fifth",
        "Market", "Church", "Spring", "Center", "River", "Sunset", "Madison",
    ]

    STREET_TYPES = ["St", "Ave", "Blvd", "Dr", "Ln", "Rd", "Way", "Ct", "Pl"]

    CITIES = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
        "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
        "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis", "Seattle",
        "Denver", "Washington", "Boston", "El Paso", "Nashville", "Detroit", "Portland",
    ]

    STATES = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    ]

    def __init__(self, seed: Optional[int] = None, locale: str = "en_US"):
        """
        Initialize the synthetic data generator.

        Args:
            seed: Random seed for reproducible generation
            locale: Locale for data generation (currently only en_US supported)
        """
        if seed is not None:
            random.seed(seed)
        self.locale = locale

    def generate_pii(
        self, entity_type: str, count: int = 1, **kwargs
    ) -> List[str]:
        """
        Generate synthetic PII of a specific type.

        Args:
            entity_type: Type of PII to generate (EMAIL, PHONE, SSN, etc.)
            count: Number of items to generate
            **kwargs: Additional parameters specific to the entity type

        Returns:
            List of generated PII values

        Example:
            >>> gen = SyntheticDataGenerator()
            >>> emails = gen.generate_pii("EMAIL", count=5)
            >>> phones = gen.generate_pii("PHONE", count=3, format="us")
            >>> ssns = gen.generate_pii("SSN", count=10)
        """
        entity_type = entity_type.upper()

        generators = {
            "NAME": self._generate_name,
            "PERSON": self._generate_name,
            "FIRST_NAME": lambda: random.choice(self.FIRST_NAMES),
            "LAST_NAME": lambda: random.choice(self.LAST_NAMES),
            "EMAIL": self._generate_email,
            "PHONE": self._generate_phone,
            "PHONE_NUMBER": self._generate_phone,
            "SSN": self._generate_ssn,
            "CREDIT_CARD": self._generate_credit_card,
            "IP_ADDRESS": self._generate_ip,
            "IPV4": self._generate_ip,
            "IPV6": self._generate_ipv6,
            "ADDRESS": self._generate_address,
            "STREET_ADDRESS": self._generate_street_address,
            "CITY": lambda: random.choice(self.CITIES),
            "STATE": lambda: random.choice(self.STATES),
            "ZIP_CODE": self._generate_zip,
            "DATE_OF_BIRTH": self._generate_dob,
            "URL": self._generate_url,
            "USERNAME": self._generate_username,
            "PASSWORD": self._generate_password,
        }

        if entity_type not in generators:
            raise ValueError(
                f"Unsupported entity type: {entity_type}. "
                f"Supported types: {', '.join(generators.keys())}"
            )

        return [generators[entity_type](**kwargs) for _ in range(count)]

    def _generate_name(self, **kwargs) -> str:
        """Generate a full name."""
        first = random.choice(self.FIRST_NAMES)
        last = random.choice(self.LAST_NAMES)
        return f"{first} {last}"

    def _generate_email(self, **kwargs) -> str:
        """Generate an email address."""
        first = random.choice(self.FIRST_NAMES).lower()
        last = random.choice(self.LAST_NAMES).lower()
        domain = random.choice(self.EMAIL_DOMAINS)

        # Different email formats
        formats = [
            f"{first}.{last}@{domain}",
            f"{first}{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}_{last}@{domain}",
            f"{first}{random.randint(1, 999)}@{domain}",
        ]

        return random.choice(formats)

    def _generate_phone(self, format_type: str = "us", **kwargs) -> str:
        """Generate a phone number."""
        if format_type == "us":
            area = random.randint(200, 999)
            exchange = random.randint(200, 999)
            number = random.randint(1000, 9999)

            formats = [
                f"{area}-{exchange}-{number}",
                f"({area}) {exchange}-{number}",
                f"{area}.{exchange}.{number}",
                f"{area}{exchange}{number}",
                f"+1-{area}-{exchange}-{number}",
            ]
            return random.choice(formats)

        elif format_type == "intl":
            country_code = random.randint(1, 999)
            number = "".join([str(random.randint(0, 9)) for _ in range(10)])
            return f"+{country_code} {number[:3]} {number[3:6]} {number[6:]}"

        return self._generate_phone(format_type="us")

    def _generate_ssn(self, **kwargs) -> str:
        """Generate a Social Security Number."""
        # Format: XXX-XX-XXXX
        # Avoid certain invalid patterns
        area = random.randint(1, 899)  # 000, 666, 900-999 are invalid
        group = random.randint(1, 99)
        serial = random.randint(1, 9999)

        return f"{area:03d}-{group:02d}-{serial:04d}"

    def _generate_credit_card(self, card_type: str = "visa", **kwargs) -> str:
        """Generate a credit card number (Luhn algorithm valid)."""
        if card_type == "visa":
            prefix = "4"
            length = 16
        elif card_type == "mastercard":
            prefix = "5" + str(random.randint(1, 5))
            length = 16
        elif card_type == "amex":
            prefix = "3" + str(random.choice([4, 7]))
            length = 15
        elif card_type == "discover":
            prefix = "6011"
            length = 16
        else:
            prefix = "4"
            length = 16

        # Generate random digits
        number = prefix + "".join([str(random.randint(0, 9)) for _ in range(length - len(prefix) - 1)])

        # Calculate Luhn check digit
        def luhn_checksum(card_number):
            def digits_of(n):
                return [int(d) for d in str(n)]

            digits = digits_of(card_number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10

        check_digit = (10 - luhn_checksum(int(number + "0"))) % 10
        return number + str(check_digit)

    def _generate_ip(self, **kwargs) -> str:
        """Generate an IPv4 address."""
        return ".".join([str(random.randint(0, 255)) for _ in range(4)])

    def _generate_ipv6(self, **kwargs) -> str:
        """Generate an IPv6 address."""
        return ":".join([f"{random.randint(0, 65535):04x}" for _ in range(8)])

    def _generate_street_address(self, **kwargs) -> str:
        """Generate a street address."""
        number = random.randint(1, 9999)
        street = random.choice(self.STREET_NAMES)
        street_type = random.choice(self.STREET_TYPES)
        return f"{number} {street} {street_type}"

    def _generate_address(self, **kwargs) -> str:
        """Generate a full address."""
        street = self._generate_street_address()
        city = random.choice(self.CITIES)
        state = random.choice(self.STATES)
        zip_code = self._generate_zip()
        return f"{street}, {city}, {state} {zip_code}"

    def _generate_zip(self, **kwargs) -> str:
        """Generate a ZIP code."""
        if random.random() < 0.5:
            return f"{random.randint(10000, 99999)}"
        else:
            return f"{random.randint(10000, 99999)}-{random.randint(1000, 9999)}"

    def _generate_dob(self, min_age: int = 18, max_age: int = 80, **kwargs) -> str:
        """Generate a date of birth."""
        today = datetime.now()
        min_date = today - timedelta(days=365 * max_age)
        max_date = today - timedelta(days=365 * min_age)

        random_days = random.randint(0, (max_date - min_date).days)
        dob = min_date + timedelta(days=random_days)

        return dob.strftime("%Y-%m-%d")

    def _generate_url(self, **kwargs) -> str:
        """Generate a URL."""
        protocols = ["http", "https"]
        domains = ["example.com", "test.org", "website.net", "company.com"]
        paths = ["", "/page", "/api/v1", "/docs", "/products", "/about"]

        protocol = random.choice(protocols)
        domain = random.choice(domains)
        path = random.choice(paths)

        return f"{protocol}://{domain}{path}"

    def _generate_username(self, **kwargs) -> str:
        """Generate a username."""
        first = random.choice(self.FIRST_NAMES).lower()
        last = random.choice(self.LAST_NAMES).lower()

        formats = [
            f"{first}{last}",
            f"{first}.{last}",
            f"{first}_{last}",
            f"{first}{random.randint(1, 999)}",
            f"{first[0]}{last}",
        ]

        return random.choice(formats)

    def _generate_password(self, length: int = 12, **kwargs) -> str:
        """Generate a password."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        return "".join(random.choice(chars) for _ in range(length))

    def generate_text_with_pii(
        self,
        template: str,
        count: int = 1,
        **entity_kwargs
    ) -> List[str]:
        """
        Generate text from a template with embedded PII.

        The template should include placeholders in curly braces for PII types.

        Args:
            template: Template string with {ENTITY_TYPE} placeholders
            count: Number of texts to generate
            **entity_kwargs: Keyword arguments for specific entity types

        Returns:
            List of generated texts

        Example:
            >>> gen = SyntheticDataGenerator()
            >>> texts = gen.generate_text_with_pii(
            ...     template="Contact {NAME} at {EMAIL} or call {PHONE}",
            ...     count=3
            ... )
            >>> print(texts[0])
            'Contact John Smith at john.smith@example.com or call 555-123-4567'
        """
        results = []

        for _ in range(count):
            text = template

            # Find all placeholders
            import re
            placeholders = re.findall(r"\{(\w+)\}", template)

            # Replace each placeholder with generated PII
            for placeholder in placeholders:
                entity_type = placeholder.upper()
                try:
                    pii_value = self.generate_pii(entity_type, count=1, **entity_kwargs)[0]
                    text = text.replace(f"{{{placeholder}}}", pii_value, 1)
                except ValueError:
                    # Keep placeholder if entity type not supported
                    pass

            results.append(text)

        return results

    def generate_dataset(
        self,
        templates: List[str],
        samples_per_template: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate a dataset with multiple templates.

        Args:
            templates: List of template strings
            samples_per_template: Number of samples to generate per template

        Returns:
            List of dictionaries containing generated data

        Example:
            >>> gen = SyntheticDataGenerator(seed=42)
            >>> templates = [
            ...     "User {NAME} ({EMAIL}) registered from {IP_ADDRESS}",
            ...     "Payment of {CREDIT_CARD} from {ADDRESS}",
            ... ]
            >>> dataset = gen.generate_dataset(templates, samples_per_template=5)
            >>> len(dataset)
            10
        """
        dataset = []

        for template_idx, template in enumerate(templates):
            texts = self.generate_text_with_pii(template, count=samples_per_template)

            for text_idx, text in enumerate(texts):
                dataset.append({
                    "id": f"{template_idx}_{text_idx}",
                    "template": template,
                    "text": text,
                })

        return dataset
