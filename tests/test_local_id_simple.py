# tests/test_local_id_simple.py

import pytest
from filu_x.core.id_generator import generate_local_id, parse_local_id

class TestLocalIDGeneration:
    """Simple unit tests for local ID logic"""
    
    def test_simple_post_default_name(self):
        """Default name is 'post' when no custom name or number given"""
        post_hash = "a1b2c3d4e5f678901234567890abcdef"
        manifest_version = "0.0.0.1"
        
        local_id = generate_local_id(post_hash, manifest_version)
        
        assert local_id == "post.0_0_0_1_a1b2c3"
        # Verify parsing works
        parsed = parse_local_id(local_id)
        assert parsed["name"] == "post"
        assert parsed["manifest_version"] == "0.0.0.1"
        assert parsed["post_fingerprint"] == "a1b2c3"
    
    def test_custom_name_sanitization(self):
        """Special characters are sanitized in custom names"""
        post_hash = "a1b2c3d4e5f678901234567890abcdef"
        manifest_version = "0.0.0.1"
        
        # Various special characters
        test_cases = [
            ("Hello World", "hello-world"),
            ("Test!!!Post", "test-post"),
            ("UPPER_CASE", "upper-case"),
            ("  spaces  ", "spaces"),
            ("a@b#c$d", "a-b-c-d"),
        ]
        
        for input_name, expected in test_cases:
            local_id = generate_local_id(post_hash, manifest_version, custom_name=input_name)
            expected_full = f"{expected}.0_0_0_1_a1b2c3"
            assert local_id == expected_full, f"Failed for input: {input_name}"
    
    def test_post_number_format(self):
        """Post number is formatted as 'post{N}'"""
        post_hash = "a1b2c3d4e5f678901234567890abcdef"
        manifest_version = "0.0.0.42"
        
        local_id = generate_local_id(post_hash, manifest_version, post_number=42)
        
        assert local_id == "post42.0_0_0_42_a1b2c3"
    
    def test_title_becomes_custom_name(self):
        """Thread title is used as custom name"""
        post_hash = "a1b2c3d4e5f678901234567890abcdef"
        manifest_version = "0.0.0.5"
        title = "My Awesome Discussion"
        
        local_id = generate_local_id(post_hash, manifest_version, custom_name=title)
        
        assert local_id == "my-awesome-discussion.0_0_0_5_a1b2c3"
    
    def test_manifest_version_underscores(self):
        """Dots in version become underscores"""
        post_hash = "a1b2c3d4e5f678901234567890abcdef"
        
        # Test various version formats
        versions = [
            ("0.0.0.1", "0_0_0_1"),
            ("1.2.3.4", "1_2_3_4"),
            ("999.999.999.999", "999_999_999_999"),
        ]
        
        for version_in, version_out in versions:
            local_id = generate_local_id(post_hash, version_in, custom_name="test")
            expected = f"test.{version_out}_a1b2c3"
            assert local_id == expected
    
    def test_post_hash_truncation(self):
        """Only first 6 chars of hash are used"""
        post_hash = "a1b2c3d4e5f678901234567890abcdef1234567890"
        manifest_version = "0.0.0.1"
        
        local_id = generate_local_id(post_hash, manifest_version)
        
        # Should use only first 6 chars
        assert local_id.endswith("_a1b2c3")
        assert "abcdef" not in local_id  # Rest of hash not included
