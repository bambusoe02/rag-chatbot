#!/bin/bash

# Test backup and restore functionality

echo "🧪 Testing backup system..."

# 1. Create test data
echo "1. Creating test data..."
mkdir -p ./data/test
echo "test data" > ./data/test/test_file.txt

# 2. Run backup
echo "2. Running backup..."
./backup.sh

# 3. Check if backup was created
LATEST_BACKUP=$(ls -t ./backups/rag_backup_*.tar.gz | head -1)
if [ -f "$LATEST_BACKUP" ]; then
    echo "✅ Backup created: $LATEST_BACKUP"
else
    echo "❌ Backup failed"
    exit 1
fi

# 4. Remove test data
echo "3. Removing test data..."
rm -rf ./data/test

# 5. Test restore (optional - requires confirmation)
echo "4. To test restore, run:"
echo "   ./restore.sh $LATEST_BACKUP"

echo ""
echo "✅ Backup test completed successfully!"

