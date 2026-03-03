# tests/integration/cli/test_post.py
import pytest
import json
import re
from click.testing import CliRunner
from filu_x.cli import cli

class TestPostCommand:
    def test_create_simple_post(self, user, runner):
        """Test creating a simple post with local ID"""
        data_dir = user["data_dir"]

        result = runner.invoke(cli, [
            '--data-dir', str(data_dir),
            'post', 'Hello world!'
        ])

        assert result.exit_code == 0
        assert "Post created" in result.output or "📝" in result.output

        # Verify post file exists
        posts_dir = data_dir / "public" / "ipfs" / "posts"
        posts = list(posts_dir.glob("*.json"))
        assert len(posts) == 1

        # Verify local ID format
        with open(posts[0]) as f:
            post_data = json.load(f)
        assert "local_id" in post_data
        local_id = post_data["local_id"]

        # Check format: post{N}.{version}_{fingerprint} where N >= 1
        pattern = r'^post\d+\.\d_\d_\d_\d_[a-f0-9]{6}$'
        assert re.match(pattern, local_id) is not None, f"Invalid local_id format: {local_id}"
        
        # Check that version is from manifest (should be 0_0_0_0 for first post)
        assert "0_0_0_0" in local_id

    def test_create_thread_post(self, user, runner):
        """Test creating a thread post with title generates correct local ID"""
        data_dir = user["data_dir"]

        result = runner.invoke(cli, [
            '--data-dir', str(data_dir),
            'post', 'Thread root content',
            '--title', 'Test Thread',
            '--description', 'Testing threads'
        ])

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Verify post
        posts_dir = data_dir / "public" / "ipfs" / "posts"
        posts = list(posts_dir.glob("*.json"))
        assert len(posts) == 1, "No post file created"

        with open(posts[0]) as f:
            post_data = json.load(f)

        # Debug output if needed
        if "post_type" not in post_data:
            print(f"DEBUG: post_data keys: {list(post_data.keys())}")
            print(f"DEBUG: full post_data: {json.dumps(post_data, indent=2)}")

        # Check thread properties
        assert "post_type" in post_data, "Missing post_type field"
        assert post_data["post_type"] == "thread"
        assert post_data["thread_title"] == "Test Thread"
        assert post_data["thread_description"] == "Testing threads"

        # Check local ID uses title
        local_id = post_data["local_id"]
        assert local_id.startswith("test-thread.")  # sanitized title
        assert "0_0_0_0" in local_id  # manifest version
        assert re.search(r'[a-f0-9]{6}$', local_id)  # hash fingerprint at the end

    def test_create_post_with_custom_local_id(self, user, runner):
        """Test creating a post with custom local ID after other posts exist"""
        data_dir = user["data_dir"]

        # Create first post (auto-numbered)
        result1 = runner.invoke(cli, [
            '--data-dir', str(data_dir),
            'post', 'First post'
        ])
        assert result1.exit_code == 0

        # Create second post (auto-numbered)
        result2 = runner.invoke(cli, [
            '--data-dir', str(data_dir),
            'post', 'Second post'
        ])
        assert result2.exit_code == 0

        # Create third post with custom ID
        result3 = runner.invoke(cli, [
            '--data-dir', str(data_dir),
            'post', 'Custom ID test',
            '--local-id', 'my-special-post'
        ])
        assert result3.exit_code == 0

        # Verify all three posts exist
        posts_dir = data_dir / "public" / "ipfs" / "posts"
        posts = list(posts_dir.glob("*.json"))
        assert len(posts) == 3

        # Load all posts and sort by created_at to get chronological order
        posts_with_data = []
        for p in posts:
            with open(p) as f:
                data = json.load(f)
            posts_with_data.append((p, data))
        posts_with_data.sort(key=lambda x: x[1]["created_at"])  # oldest first

        # Check the custom post (should be the third one)
        post1_data = posts_with_data[0][1]
        post2_data = posts_with_data[1][1]
        post3_data = posts_with_data[2][1]

        local_id = post3_data["local_id"]
        assert local_id.startswith("my-special-post.")
        assert "0_0_0_0" in local_id  # manifest version (still 0.0.0.0 for all posts)
        assert re.search(r'[a-f0-9]{6}$', local_id)
        
        name_part = local_id.split('.')[0]
        assert name_part == "my-special-post"

        # Verify the first two posts have correct auto-numbered IDs
        assert post1_data["local_id"].startswith("post1.")
        assert post2_data["local_id"].startswith("post2.")

    def test_multiple_posts_increment_numbers(self, user, runner):
        """Test that post numbers increment correctly"""
        data_dir = user["data_dir"]

        # Create first post
        result1 = runner.invoke(cli, ['--data-dir', str(data_dir), 'post', 'First post'])
        assert result1.exit_code == 0

        # Create second post
        result2 = runner.invoke(cli, ['--data-dir', str(data_dir), 'post', 'Second post'])
        assert result2.exit_code == 0

        # Get both posts and sort by creation date
        posts_dir = data_dir / "public" / "ipfs" / "posts"
        posts = list(posts_dir.glob("*.json"))
        posts_with_data = []
        for p in posts:
            with open(p) as f:
                data = json.load(f)
            posts_with_data.append((p, data))
        posts_with_data.sort(key=lambda x: x[1]["created_at"])

        with open(posts_with_data[0][0]) as f:
            post1 = json.load(f)
        with open(posts_with_data[1][0]) as f:
            post2 = json.load(f)

        # First post should be post1, second post should be post2
        assert post1["local_id"].startswith("post1.")
        assert post2["local_id"].startswith("post2.")

    def test_local_mapping_file_created(self, user, runner):
        """Test that mapping.json is created with correct entries"""
        data_dir = user["data_dir"]

        # Create a post
        runner.invoke(cli, ['--data-dir', str(data_dir), 'post', 'Test mapping'])

        # Check mapping file
        mapping_file = data_dir / "local" / "mapping.json"
        assert mapping_file.exists()

        with open(mapping_file) as f:
            mapping = json.load(f)

        assert len(mapping) == 1
        local_id = list(mapping.keys())[0]
        
        # Verify mapping structure
        entry = mapping[local_id]
        assert "post_id" in entry
        assert "manifest_version" in entry
        assert "created_at" in entry
        assert "path" in entry
        assert "post_type" in entry
        assert entry["post_type"] == "simple"

    def test_local_file_created(self, user, runner):
        """Test that post is also saved in local/posts/ directory"""
        data_dir = user["data_dir"]

        # Create a post
        result = runner.invoke(cli, ['--data-dir', str(data_dir), 'post', 'Test local copy'])
        assert result.exit_code == 0

        # Extract local_id from output
        match = re.search(r'created: ([^\s]+)', result.output)
        assert match, "Could not find local_id in output"
        local_id = match.group(1).strip()

        # Check local file exists
        local_path = data_dir / "local" / "posts" / local_id
        assert local_path.exists()

        # Verify content matches
        with open(local_path) as f:
            local_data = json.load(f)
        assert local_data["content"] == "Test local copy"
