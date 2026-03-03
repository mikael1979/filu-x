"""End-to-end test for basic flow"""
import pytest
from click.testing import CliRunner
from filu_x.cli import cli

class TestBasicFlow:
    def test_create_and_sync_post(self, temp_dir):
        """Test creating a post and syncing it"""
        runner = CliRunner()
        
        # Initialize user
        runner.invoke(cli, [
            '--data-dir', str(temp_dir),
            'init', 'alice', '--no-password'
        ])
        
        # Create post
        result = runner.invoke(cli, [
            '--data-dir', str(temp_dir),
            'post', 'Hello world!'
        ])
        assert result.exit_code == 0
        assert "Post created" in result.output
        
        # Sync to IPFS
        result = runner.invoke(cli, [
            '--data-dir', str(temp_dir),
            'sync'
        ])
        assert result.exit_code == 0
        
        # Check feed
        result = runner.invoke(cli, [
            '--data-dir', str(temp_dir),
            'feed'
        ])
        assert result.exit_code == 0
        assert "Hello world!" in result.output
