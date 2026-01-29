#!/bin/bash

# RAG Chatbot Restore Script
# Restores data from backup archive

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔄 RAG Chatbot Restore Utility${NC}"
echo ""

BACKUP_DIR="./backups"
DATA_DIR="./data"
RESTORE_TEMP="./restore_temp"

# Function to list available backups
list_backups() {
    echo -e "${YELLOW}Available backups:${NC}"
    echo ""
    
    if [ ! -d "${BACKUP_DIR}" ] || [ -z "$(ls -A ${BACKUP_DIR}/*.tar.gz 2>/dev/null)" ]; then
        echo -e "${RED}No backups found in ${BACKUP_DIR}${NC}"
        exit 1
    fi
    
    local index=1
    for backup in ${BACKUP_DIR}/rag_backup_*.tar.gz; do
        if [ -f "$backup" ]; then
            local filename=$(basename "$backup")
            local size=$(du -sh "$backup" | cut -f1)
            local date=$(echo "$filename" | sed 's/rag_backup_\(.*\)\.tar\.gz/\1/' | sed 's/_/ /g')
            echo -e "${index}. ${filename}"
            echo -e "   📅 Date: ${date}"
            echo -e "   💾 Size: ${size}"
            echo ""
            index=$((index + 1))
        fi
    done
}

# Function to verify backup
verify_backup() {
    local backup_file=$1
    echo -e "${YELLOW}🔍 Verifying backup integrity...${NC}"
    
    if ! tar -tzf "${backup_file}" > /dev/null 2>&1; then
        echo -e "${RED}❌ Backup file is corrupted!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Backup integrity verified${NC}"
}

# Function to show backup contents
show_contents() {
    local backup_file=$1
    echo -e "${YELLOW}📦 Backup contents:${NC}"
    tar -tzf "${backup_file}" | head -20
    echo ""
}

# Function to perform restore
perform_restore() {
    local backup_file=$1
    
    echo -e "${RED}⚠️  WARNING: This will overwrite existing data!${NC}"
    echo -e "${YELLOW}Current data will be backed up to ${DATA_DIR}.backup_$(date +%s)${NC}"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Restore cancelled${NC}"
        exit 0
    fi
    
    # Create backup of current data
    echo -e "${YELLOW}💾 Backing up current data...${NC}"
    if [ -d "${DATA_DIR}" ]; then
        mv "${DATA_DIR}" "${DATA_DIR}.backup_$(date +%s)"
        echo -e "${GREEN}✅ Current data backed up${NC}"
    fi
    
    # Stop services (Docker)
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    docker-compose down 2>/dev/null || echo "Services not running"
    
    # Extract backup
    echo -e "${YELLOW}📦 Extracting backup...${NC}"
    rm -rf "${RESTORE_TEMP}"
    mkdir -p "${RESTORE_TEMP}"
    tar -xzf "${backup_file}" -C "${RESTORE_TEMP}"
    
    # Find extracted directory
    EXTRACTED_DIR=$(find "${RESTORE_TEMP}" -mindepth 1 -maxdepth 1 -type d)
    
    if [ -z "$EXTRACTED_DIR" ]; then
        echo -e "${RED}❌ Failed to extract backup${NC}"
        exit 1
    fi
    
    # Restore database
    if [ -f "${EXTRACTED_DIR}/app.db" ]; then
        echo -e "${YELLOW}💾 Restoring database...${NC}"
        mkdir -p "${DATA_DIR}"
        cp "${EXTRACTED_DIR}/app.db" "${DATA_DIR}/"
        echo -e "${GREEN}✅ Database restored${NC}"
    fi
    
    # Restore ChromaDB
    if [ -d "${EXTRACTED_DIR}/chroma_db" ]; then
        echo -e "${YELLOW}🔍 Restoring ChromaDB...${NC}"
        mkdir -p "${DATA_DIR}"
        cp -r "${EXTRACTED_DIR}/chroma_db" "${DATA_DIR}/"
        echo -e "${GREEN}✅ ChromaDB restored${NC}"
    fi
    
    # Restore uploads
    if [ -d "${EXTRACTED_DIR}/uploads" ]; then
        echo -e "${YELLOW}📄 Restoring uploaded files...${NC}"
        mkdir -p "${DATA_DIR}"
        cp -r "${EXTRACTED_DIR}/uploads" "${DATA_DIR}/"
        FILES_COUNT=$(find "${DATA_DIR}/uploads" -type f | wc -l)
        echo -e "${GREEN}✅ Uploaded files restored (${FILES_COUNT} files)${NC}"
    fi
    
    # Restore chat history
    if [ -d "${EXTRACTED_DIR}/chat_history" ]; then
        echo -e "${YELLOW}💬 Restoring chat history...${NC}"
        mkdir -p "${DATA_DIR}"
        cp -r "${EXTRACTED_DIR}/chat_history" "${DATA_DIR}/"
        echo -e "${GREEN}✅ Chat history restored${NC}"
    fi
    
    # Restore analytics
    if [ -d "${EXTRACTED_DIR}/analytics" ]; then
        echo -e "${YELLOW}📊 Restoring analytics...${NC}"
        mkdir -p "${DATA_DIR}"
        cp -r "${EXTRACTED_DIR}/analytics" "${DATA_DIR}/"
        echo -e "${GREEN}✅ Analytics restored${NC}"
    fi
    
    # Restore feedback
    if [ -d "${EXTRACTED_DIR}/feedback" ]; then
        echo -e "${YELLOW}👍 Restoring feedback...${NC}"
        mkdir -p "${DATA_DIR}"
        cp -r "${EXTRACTED_DIR}/feedback" "${DATA_DIR}/"
        echo -e "${GREEN}✅ Feedback restored${NC}"
    fi
    
    # Show backup info
    if [ -f "${EXTRACTED_DIR}/backup_info.txt" ]; then
        echo ""
        echo -e "${YELLOW}📝 Backup Information:${NC}"
        cat "${EXTRACTED_DIR}/backup_info.txt"
        echo ""
    fi
    
    # Cleanup
    echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
    rm -rf "${RESTORE_TEMP}"
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    
    # Set correct permissions
    echo -e "${YELLOW}🔐 Setting permissions...${NC}"
    chmod -R 755 "${DATA_DIR}" 2>/dev/null || true
    echo -e "${GREEN}✅ Permissions set${NC}"
    
    # Restart services
    echo -e "${YELLOW}🚀 Starting services...${NC}"
    docker-compose up -d 2>/dev/null || echo "Docker not available, services not started"
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ RESTORE COMPLETED SUCCESSFULLY!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Services are starting up...${NC}"
    echo -e "Check status with: ${GREEN}docker-compose ps${NC}"
    echo -e "View logs with: ${GREEN}docker-compose logs -f${NC}"
    echo ""
}

# Main script logic
if [ $# -eq 0 ]; then
    # No arguments - show menu
    list_backups
    echo ""
    read -p "Enter backup number to restore (or 'q' to quit): " choice
    
    if [ "$choice" = "q" ]; then
        exit 0
    fi
    
    # Get backup file by index
    backup_files=(${BACKUP_DIR}/rag_backup_*.tar.gz)
    backup_file=${backup_files[$((choice-1))]}
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}Invalid selection${NC}"
        exit 1
    fi
else
    # Backup file provided as argument
    if [ -f "$1" ]; then
        backup_file="$1"
    elif [ -f "${BACKUP_DIR}/$1" ]; then
        backup_file="${BACKUP_DIR}/$1"
    else
        echo -e "${RED}Backup file not found: $1${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Selected backup:${NC} $(basename ${backup_file})"
echo ""

verify_backup "${backup_file}"
show_contents "${backup_file}"
perform_restore "${backup_file}"

