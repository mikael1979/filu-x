"""Unit tests for IPFS client"""
import pytest
from filu_x.core.ipfs_client import IPFSClient

class TestIPFSClient:
    def test_init_auto_mode(self):
        """Test auto mode initialization"""
        client = IPFSClient(mode="auto")
        assert client.mode == "auto"
    
    def test_init_mock_mode(self):
        """Test mock mode initialization"""
        client = IPFSClient(mode="mock")
        assert client.mode == "mock"
        assert not client.use_real
    
    def test_mock_add_file(self, temp_dir):
        """Test mock add file"""
        client = IPFSClient(mode="mock")
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello world")
        
        cid = client.add_file(test_file)
        assert cid.startswith("Qm") or cid.startswith("bafk")
        assert len(cid) > 10
    
    def test_mock_cat(self, temp_dir):
        """Test mock cat"""
        client = IPFSClient(mode="mock")
        test_file = temp_dir / "test.txt"
        content = b"Hello world"
        test_file.write_bytes(content)
        
        cid = client.add_file(test_file)
        retrieved = client.cat(cid)
        assert retrieved == content
