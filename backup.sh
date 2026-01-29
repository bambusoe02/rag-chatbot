#!/bin/bash

# RAG Chatbot Backup Script
# Creates timestamped backup of all critical data

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔄 Starting RAG Chatbot Backup...${NC}"

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_NAME="rag_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
DATA_DIR="./data"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Create temporary backup directory
mkdir -p "${BACKUP_PATH}"

echo -e "${YELLOW}📦 Backup destination: ${BACKUP_PATH}${NC}"

# 1. Backup SQLite Database
echo -e "${YELLOW}💾 Backing up SQLite database...${NC}"
if [ -f "${DATA_DIR}/app.db" ]; then
    sqlite3 "${DATA_DIR}/app.db" ".backup '${BACKUP_PATH}/app.db'"
    echo -e "${GREEN}✅ Database backed up${NC}"
else
    echo -e "${RED}⚠️  Database not found, skipping${NC}"
fi

# 2. Backup ChromaDB (vector database)
echo -e "${YELLOW}🔍 Backing up ChromaDB...${NC}"
if [ -d "${DATA_DIR}/chroma_db" ]; then
    cp -r "${DATA_DIR}/chroma_db" "${BACKUP_PATH}/"
    CHROMA_SIZE=$(du -sh "${BACKUP_PATH}/chroma_db" | cut -f1)
    echo -e "${GREEN}✅ ChromaDB backed up (${CHROMA_SIZE})${NC}"
else
    echo -e "${RED}⚠️  ChromaDB not found, skipping${NC}"
fi

# 3. Backup uploaded files
echo -e "${YELLOW}📄 Backing up uploaded files...${NC}"
if [ -d "${DATA_DIR}/uploads" ]; then
    cp -r "${DATA_DIR}/uploads" "${BACKUP_PATH}/"
    FILES_COUNT=$(find "${BACKUP_PATH}/uploads" -type f | wc -l)
    FILES_SIZE=$(du -sh "${BACKUP_PATH}/uploads" | cut -f1)
    echo -e "${GREEN}✅ Uploaded files backed up (${FILES_COUNT} files, ${FILES_SIZE})${NC}"
else
    echo -e "${RED}⚠️  Uploads directory not found, skipping${NC}"
fi

# 4. Backup chat history
echo -e "${YELLOW}💬 Backing up chat history...${NC}"
if [ -d "${DATA_DIR}/chat_history" ]; then
    cp -r "${DATA_DIR}/chat_history" "${BACKUP_PATH}/"
    echo -e "${GREEN}✅ Chat history backed up${NC}"
else
    echo -e "${YELLOW}⚠️  Chat history not found, skipping${NC}"
fi

# 5. Backup analytics data
echo -e "${YELLOW}📊 Backing up analytics...${NC}"
if [ -d "${DATA_DIR}/analytics" ]; then
    cp -r "${DATA_DIR}/analytics" "${BACKUP_PATH}/"
    echo -e "${GREEN}✅ Analytics backed up${NC}"
else
    echo -e "${YELLOW}⚠️  Analytics not found, skipping${NC}"
fi

# 6. Backup feedback data
echo -e "${YELLOW}👍 Backing up feedback...${NC}"
if [ -d "${DATA_DIR}/feedback" ]; then
    cp -r "${DATA_DIR}/feedback" "${BACKUP_PATH}/"
    echo -e "${GREEN}✅ Feedback backed up${NC}"
else
    echo -e "${YELLOW}⚠️  Feedback not found, skipping${NC}"
fi

# 7. Copy environment file (without secrets)
echo -e "${YELLOW}⚙️  Backing up configuration...${NC}"
if [ -f ".env" ]; then
    # Backup .env but redact sensitive values
    grep -v "SECRET_KEY\|PASSWORD\|API_KEY" .env > "${BACKUP_PATH}/.env.template" 2>/dev/null || true
    echo -e "${GREEN}✅ Configuration template backed up${NC}"
fi

# 8. Create metadata file
echo -e "${YELLOW}📝 Creating backup metadata...${NC}"
cat > "${BACKUP_PATH}/backup_info.txt" << EOF
RAG Chatbot Backup
==================
Timestamp: ${TIMESTAMP}
Date: $(date)
Hostname: $(hostname)
User: $(whoami)

Contents:
- SQLite Database: $([ -f "${BACKUP_PATH}/app.db" ] && echo "✅" || echo "❌")
- ChromaDB: $([ -d "${BACKUP_PATH}/chroma_db" ] && echo "✅" || echo "❌")
- Uploaded Files: $([ -d "${BACKUP_PATH}/uploads" ] && echo "✅" || echo "❌")
- Chat History: $([ -d "${BACKUP_PATH}/chat_history" ] && echo "✅" || echo "❌")
- Analytics: $([ -d "${BACKUP_PATH}/analytics" ] && echo "✅" || echo "❌")
- Feedback: $([ -d "${BACKUP_PATH}/feedback" ] && echo "✅" || echo "❌")

Sizes:
EOF

du -sh "${BACKUP_PATH}"/* >> "${BACKUP_PATH}/backup_info.txt" 2>/dev/null || true

echo -e "${GREEN}✅ Metadata created${NC}"

# 9. Compress backup
echo -e "${YELLOW}📦 Compressing backup...${NC}"
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"
cd - > /dev/null

BACKUP_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
echo -e "${GREEN}✅ Backup compressed: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})${NC}"

# 10. Verify backup integrity
echo -e "${YELLOW}🔍 Verifying backup integrity...${NC}"
if tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backup integrity verified${NC}"
else
    echo -e "${RED}❌ Backup verification failed!${NC}"
    exit 1
fi

# 11. Cleanup old backups (keep last 7 days)
echo -e "${YELLOW}🧹 Cleaning up old backups (keeping last 7)...${NC}"
cd "${BACKUP_DIR}"
ls -t rag_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm
REMAINING=$(ls -1 rag_backup_*.tar.gz 2>/dev/null | wc -l)
echo -e "${GREEN}✅ Cleanup complete (${REMAINING} backups remaining)${NC}"
cd - > /dev/null

# 12. Optional: Upload to cloud storage (S3/Google Cloud/etc)
if [ ! -z "${BACKUP_S3_BUCKET}" ]; then
    echo -e "${YELLOW}☁️  Uploading to cloud storage...${NC}"
    # Uncomment and configure for your cloud provider:
    # aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" "s3://${BACKUP_S3_BUCKET}/"
    # gsutil cp "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" "gs://${BACKUP_GCS_BUCKET}/"
    echo -e "${YELLOW}⚠️  Cloud upload not configured${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ BACKUP COMPLETED SUCCESSFULLY!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "📦 Backup file: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo -e "💾 Size: ${BACKUP_SIZE}"
echo -e "📅 Date: $(date)"
echo ""
echo -e "${YELLOW}To restore this backup, run:${NC}"
echo -e "  ./restore.sh ${BACKUP_NAME}.tar.gz"
echo ""

