# tests/integration/cli/test_init.py
import pytest
from click.testing import CliRunner
from filu_x.cli import cli

class TestInitCommand:
    def test_init_new_user(self, data_dir, runner):
        """Test initializing a new user"""
        result = runner.invoke(cli, [
            '--data-dir', str(data_dir),
            'init', 'testuser', '--no-password'
        ])
        
        assert result.exit_code == 0
        assert "Filu-X initialized" in result.output
        
        # Check that files were created
        profile_path = data_dir / "public" / "ipfs" / "profile.json"
        assert profile_path.exists()
        
        manifest_path = data_dir / "public" / "ipfs" / "Filu-X.json"
        assert manifest_path.exists()
    
    def test_init_existing_user(self, data_dir, user, runner):
        """Test initializing an already initialized user"""
        # user fixture already created a user in data_dir
        result = runner.invoke(cli, [
            '--data-dir', str(data_dir),
            'init', 'another', '--no-password'
        ])
        
        # Should exit with error code 1 because user already exists
        assert result.exit_code == 1
        assert "already initialized" in result.output
