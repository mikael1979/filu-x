#!/bin/bash

# Filu-X Project Code Collector v2.1
# Collects .py files, JSON schemas, specs, and client code into a single document

OUTPUT_FILE="filu-x_code_collection_$(date +%Y%m%d_%H%M%S).md"
SOURCE_DIR="clients"
PROTOCOLS_DIR="protocols"
SPEC_DIR="spec"
TOOLS_DIR="tools"
EXAMPLES_DIR="examples"
PROJECT_ROOT="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Collecting Filu-X project code...${NC}"
echo -e "   ${YELLOW}Source:${NC} $SOURCE_DIR"
echo -e "   ${YELLOW}Protocols:${NC} $PROTOCOLS_DIR"
echo -e "   ${YELLOW}Specs:${NC} $SPEC_DIR"
echo -e "   ${YELLOW}Tools:${NC} $TOOLS_DIR"
echo -e "   ${YELLOW}Examples:${NC} $EXAMPLES_DIR"
echo -e "   ${YELLOW}Output:${NC} $OUTPUT_FILE"

# Initialize file with proper date
cat > "$OUTPUT_FILE" << EOF
# Filu-X Project Code Collection

**Generated:** $(date -Iseconds)
**Version:** 0.1.0
**Structure:** Multi-client / Protocol-plugin architecture

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Clients](#clients)
3. [Protocols](#protocols)
4. [Specifications](#specifications)
5. [Tools](#tools)
6. [Examples](#examples)
7. [JSON Schemas](#json-schemas)

---

## Project Structure

\`\`\`
EOF

# ========== PROJECT STRUCTURE ==========
if command -v tree &> /dev/null; then
    tree -I '.venv|.git|__pycache__|*.pyc|.pytest_cache|node_modules|dist|build|*.egg-info|.env|.gitkeep' \
         --dirsfirst "$PROJECT_ROOT" >> "$OUTPUT_FILE" 2>/dev/null
else
    find "$PROJECT_ROOT" \
        -not -path '*/\.*' \
        -not -path '*/__pycache__/*' \
        -not -path '*/.venv/*' \
        -not -path '*/.git/*' \
        -not -path '*/dist/*' \
        -not -path '*/build/*' \
        -not -path '*/node_modules/*' \
        -not -path '*/.env' \
        -not -name '*.pyc' \
        -not -name '*.pyo' \
        -not -name '*.egg-info' \
        -not -name '.gitkeep' \
        | sort -f | \
        sed -e "s/[^-][^\/]*\//  |/g" -e "s/|\([^ ]\)/|-\1/" >> "$OUTPUT_FILE" 2>/dev/null
fi

echo '```' >> "$OUTPUT_FILE"

# ========== COUNTER FUNCTIONS ==========
count_files() {
    find "$1" -name "$2" 2>/dev/null | wc -l
}

count_lines() {
    find "$1" -name "$2" -exec wc -l {} + 2>/dev/null | awk '{sum+=$1} END{print sum}'
}

# Initialize counters
TOTAL_FILES=0
TOTAL_LINES=0

# ========== CLIENTS ==========
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE" 
echo "" >> "$OUTPUT_FILE"
echo "## Clients" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

for client in cli web mobile; do
    CLIENT_DIR="$SOURCE_DIR/$client"
    if [ -d "$CLIENT_DIR" ]; then
        echo "" >> "$OUTPUT_FILE"
        echo "### $client Client" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        # Count files in this client
        CLIENT_FILES=$(find "$CLIENT_DIR" -type f -not -path '*/\.*' 2>/dev/null | wc -l)
        TOTAL_FILES=$((TOTAL_FILES + CLIENT_FILES))
        
        find "$CLIENT_DIR" -type f -not -path '*/\.*' | sort | while read -r file; do
            # Skip binary files and empty files
            if file "$file" | grep -q "text"; then
                echo -e "   ${GREEN}📄 Processing:${NC} $file"
                
                EXT="${file##*.}"
                case $EXT in
                    py) LANG="python" ;;
                    js) LANG="javascript" ;;
                    ts) LANG="typescript" ;;
                    jsx) LANG="jsx" ;;
                    tsx) LANG="tsx" ;;
                    json) LANG="json" ;;
                    md) LANG="markdown" ;;
                    sh) LANG="bash" ;;
                    *) LANG="" ;;
                esac
                
                # Count lines
                FILE_LINES=$(wc -l < "$file")
                TOTAL_LINES=$((TOTAL_LINES + FILE_LINES))
                
                echo "" >> "$OUTPUT_FILE"
                echo "#### $file ($FILE_LINES lines)" >> "$OUTPUT_FILE"
                echo "" >> "$OUTPUT_FILE"
                
                if [ -n "$LANG" ]; then
                    echo "\`\`\`$LANG" >> "$OUTPUT_FILE"
                else
                    echo '```' >> "$OUTPUT_FILE"
                fi
                
                cat "$file" >> "$OUTPUT_FILE"
                echo '```' >> "$OUTPUT_FILE"
            fi
        done
    fi
done

# ========== PROTOCOLS ==========
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## Protocols" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ -d "$PROTOCOLS_DIR" ]; then
    # Core protocols
    if [ -d "$PROTOCOLS_DIR/core" ]; then
        echo "" >> "$OUTPUT_FILE"
        echo "### Core Protocols" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        find "$PROTOCOLS_DIR/core" -type f -not -path '*/\.*' | sort | while read -r file; do
            if file "$file" | grep -q "text"; then
                echo -e "   ${BLUE}🔌 Processing:${NC} $file"
                
                FILE_LINES=$(wc -l < "$file")
                TOTAL_LINES=$((TOTAL_LINES + FILE_LINES))
                TOTAL_FILES=$((TOTAL_FILES + 1))
                
                echo "" >> "$OUTPUT_FILE"
                echo "#### $file ($FILE_LINES lines)" >> "$OUTPUT_FILE"
                echo "" >> "$OUTPUT_FILE"
                
                if [[ "$file" == *.md ]]; then
                    echo '```markdown' >> "$OUTPUT_FILE"
                elif [[ "$file" == *.json ]]; then
                    echo '```json' >> "$OUTPUT_FILE"
                else
                    echo '```' >> "$OUTPUT_FILE"
                fi
                
                cat "$file" >> "$OUTPUT_FILE"
                echo '```' >> "$OUTPUT_FILE"
            fi
        done
    fi
    
    # Plugin protocols
    if [ -d "$PROTOCOLS_DIR/plugins" ]; then
        echo "" >> "$OUTPUT_FILE"
        echo "### Protocol Plugins" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        find "$PROTOCOLS_DIR/plugins" -type f -not -path '*/\.*' | sort | while read -r file; do
            if file "$file" | grep -q "text"; then
                echo -e "   ${BLUE}🔌 Processing:${NC} $file"
                
                FILE_LINES=$(wc -l < "$file")
                TOTAL_LINES=$((TOTAL_LINES + FILE_LINES))
                TOTAL_FILES=$((TOTAL_FILES + 1))
                
                echo "" >> "$OUTPUT_FILE"
                echo "#### $file ($FILE_LINES lines)" >> "$OUTPUT_FILE"
                echo "" >> "$OUTPUT_FILE"
                
                if [[ "$file" == *.md ]]; then
                    echo '```markdown' >> "$OUTPUT_FILE"
                elif [[ "$file" == *.json ]]; then
                    echo '```json' >> "$OUTPUT_FILE"
                else
                    echo '```' >> "$OUTPUT_FILE"
                fi
                
                cat "$file" >> "$OUTPUT_FILE"
                echo '```' >> "$OUTPUT_FILE"
            fi
        done
    fi
fi

# ========== SPECIFICATIONS ==========
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## Specifications" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ -d "$SPEC_DIR" ]; then
    find "$SPEC_DIR" -type f -not -path '*/\.*' | sort | while read -r file; do
        if file "$file" | grep -q "text"; then
            echo -e "   ${YELLOW}📋 Processing:${NC} $file"
            
            FILE_LINES=$(wc -l < "$file")
            TOTAL_LINES=$((TOTAL_LINES + FILE_LINES))
            TOTAL_FILES=$((TOTAL_FILES + 1))
            
            echo "" >> "$OUTPUT_FILE"
            echo "### $file ($FILE_LINES lines)" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
            
            if [[ "$file" == *.json ]]; then
                echo '```json' >> "$OUTPUT_FILE"
            else
                echo '```markdown' >> "$OUTPUT_FILE"
            fi
            
            cat "$file" >> "$OUTPUT_FILE"
            echo '```' >> "$OUTPUT_FILE"
        fi
    done
fi

# ========== TOOLS ==========
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## Tools" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ -d "$TOOLS_DIR" ]; then
    find "$TOOLS_DIR" -type f -not -path '*/\.*' | sort | while read -r file; do
        if file "$file" | grep -q "text"; then
            echo -e "   ${RED}🛠️  Processing:${NC} $file"
            
            FILE_LINES=$(wc -l < "$file")
            TOTAL_LINES=$((TOTAL_LINES + FILE_LINES))
            TOTAL_FILES=$((TOTAL_FILES + 1))
            
            echo "" >> "$OUTPUT_FILE"
            echo "### $file ($FILE_LINES lines)" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
            
            if [[ "$file" == *.py ]]; then
                echo '```python' >> "$OUTPUT_FILE"
            elif [[ "$file" == *.sh ]]; then
                echo '```bash' >> "$OUTPUT_FILE"
            else
                echo '```' >> "$OUTPUT_FILE"
            fi
            
            cat "$file" >> "$OUTPUT_FILE"
            echo '```' >> "$OUTPUT_FILE"
        fi
    done
fi

# ========== EXAMPLES ==========
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## Examples" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ -d "$EXAMPLES_DIR" ]; then
    find "$EXAMPLES_DIR" -name "*.json" | sort | while read -r file; do
        echo -e "   ${GREEN}📚 Processing:${NC} $file"
        
        FILE_LINES=$(wc -l < "$file")
        TOTAL_LINES=$((TOTAL_LINES + FILE_LINES))
        TOTAL_FILES=$((TOTAL_FILES + 1))
        
        echo "" >> "$OUTPUT_FILE"
        echo "### $file ($FILE_LINES lines)" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo '```json' >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo '```' >> "$OUTPUT_FILE"
    done
fi

# ========== JSON SCHEMAS ==========
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## JSON Schemas" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

find "$PROJECT_ROOT" -name "*.schema.json" -o -name "schema.json" 2>/dev/null | sort | while read -r file; do
    echo -e "   ${YELLOW}📐 Processing:${NC} $file"
    
    FILE_LINES=$(wc -l < "$file")
    TOTAL_LINES=$((TOTAL_LINES + FILE_LINES))
    TOTAL_FILES=$((TOTAL_FILES + 1))
    
    echo "" >> "$OUTPUT_FILE"
    echo "### $file ($FILE_LINES lines)" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo '```json' >> "$OUTPUT_FILE"
    cat "$file" >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
done

# ========== SUMMARY ==========
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## Summary" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Calculate statistics with new counters
PYTHON_FILES=$(find "$SOURCE_DIR" "$PROTOCOLS_DIR" "$TOOLS_DIR" -name "*.py" 2>/dev/null | wc -l)
JS_FILES=$(find "$SOURCE_DIR" -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" 2>/dev/null | wc -l)
JSON_FILES=$(find "$EXAMPLES_DIR" "$SPEC_DIR" "$PROJECT_ROOT" -name "*.json" 2>/dev/null | wc -l)
MD_FILES=$(find "$SPEC_DIR" "$PROTOCOLS_DIR" -name "*.md" 2>/dev/null | wc -l)
SH_FILES=$(find "$TOOLS_DIR" -name "*.sh" 2>/dev/null | wc -l)

echo "### Statistics" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- **Total files collected:** $TOTAL_FILES" >> "$OUTPUT_FILE"
echo "- **Total lines of code:** $TOTAL_LINES" >> "$OUTPUT_FILE"
echo "- **Python files:** $PYTHON_FILES" >> "$OUTPUT_FILE"
echo "- **JavaScript/TypeScript files:** $JS_FILES" >> "$OUTPUT_FILE"
echo "- **JSON examples/schemas:** $JSON_FILES" >> "$OUTPUT_FILE"
echo "- **Markdown documentation:** $MD_FILES" >> "$OUTPUT_FILE"
echo "- **Shell scripts:** $SH_FILES" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "### File Size" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- **Output file:** $(du -h "$OUTPUT_FILE" | cut -f1)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "*End of Filu-X code collection - Generated on $(date)*" >> "$OUTPUT_FILE"

# Final output
echo ""
echo -e "${GREEN}✅ Collection complete!${NC}"
echo -e "   File: ${YELLOW}$OUTPUT_FILE${NC}"
echo -e "   Size: ${BLUE}$(du -h "$OUTPUT_FILE" | cut -f1)${NC}"
echo -e "   Files collected: ${BLUE}$TOTAL_FILES${NC}"
echo -e "   Lines of code: ${BLUE}$TOTAL_LINES${NC}"
echo ""
echo -e "${YELLOW}📊 Breakdown:${NC}"
echo -e "   • Python files: ${GREEN}$PYTHON_FILES${NC}"
echo -e "   • JS/TS files: ${GREEN}$JS_FILES${NC}"
echo -e "   • JSON files: ${GREEN}$JSON_FILES${NC}"
echo -e "   • Markdown docs: ${GREEN}$MD_FILES${NC}"
echo -e "   • Shell scripts: ${GREEN}$SH_FILES${NC}"
echo ""
echo -e "${BLUE}💡 Copy the content of this file when uploading to AI assistants.${NC}"
