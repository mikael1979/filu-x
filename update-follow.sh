#!/bin/bash
# Script to update a followed user with a new profile CID
# Usage: ./update-follow.sh <follower_dir> <username_to_update> <new_profile_cid>

set -e

FOLLOWER_DIR="$1"
USERNAME="$2"
NEW_CID="$3"

if [ -z "$FOLLOWER_DIR" ] || [ -z "$USERNAME" ] || [ -z "$NEW_CID" ]; then
    echo "Usage: $0 <follower_dir> <username> <new_profile_cid>"
    echo "Example: $0 ./test_data/bob alice bafkreigiq2futyxfzsnqao6oxbslwtmofiyyub4isvzxoixjpatrvzg2rq"
    exit 1
fi

FOLLOW_LIST="$FOLLOWER_DIR/data/public/follow_list.json"

if [ ! -f "$FOLLOW_LIST" ]; then
    echo "❌ Follow list not found: $FOLLOW_LIST"
    exit 1
fi

echo "📋 Current follow list:"
jq '.follows[] | {user, profile_cid}' "$FOLLOW_LIST"

# Create backup
cp "$FOLLOW_LIST" "$FOLLOW_LIST.bak"
echo "✅ Backup created: $FOLLOW_LIST.bak"

# Update the follow entry for the specified user
jq --arg user "$USERNAME" --arg cid "$NEW_CID" '
  .follows = [
    .follows[] | 
    if .user == "@\($user)" or .user == $user then
      .profile_cid = $cid
    else
      .
    end
  ]
' "$FOLLOW_LIST" > "$FOLLOW_LIST.tmp" && mv "$FOLLOW_LIST.tmp" "$FOLLOW_LIST"

echo "✅ Updated follow list:"
jq --arg user "$USERNAME" '.follows[] | select(.user == "@\($user)" or .user == $user)' "$FOLLOW_LIST"

echo
echo "💡 Next steps:"
echo "   cd $FOLLOWER_DIR"
echo "   filu-x sync-followed -v"
echo "   filu-x feed"
