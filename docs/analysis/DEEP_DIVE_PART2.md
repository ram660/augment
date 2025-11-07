# Deep-Dive Integration Guide: Part 2
## Technologies #3-6: Docling, Skills, Agent Lightning, and Commerce

**Continuation from Part 1**

---

## Technology #3: IBM Docling
### RAG Enhancement for Building Codes & Technical Documentation

### 🎯 Current RAG System Analysis

**Your Current RAG Implementation:**
```python
# backend/services/rag_service.py
class RAGService:
    """
    Current implementation:
    - Gemini Text Embedding 004 for embeddings
    - Hybrid retrieval (vector + keyword)
    - Simple text chunking
    - Context assembly for chat
    """
    
    async def index_home_data(self, home_id: str):
        """
        Current data sources:
        - Home metadata
        - Room descriptions
        - Floor plan analyses
        - Image analyses
        - Materials and fixtures
        """
```

**Current Limitations:**
1. ❌ **No complex PDF parsing** - Can't ingest building codes
2. ❌ **No table extraction** - Loses structured data from docs
3. ❌ **Basic text chunking** - Misses document structure
4. ❌ **No formula support** - Can't parse technical calculations
5. ❌ **Limited formats** - Text-only, no advanced document understanding

---

### 🔧 Integration Implementation

#### **Integration #1: Enhanced RAG Service with Docling**

**New Service:**
```python
# backend/services/enhanced_rag_service.py (NEW FILE)
from docling.document_converter import DocumentConverter
from docling.datamodel.document import DoclingDocument
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedRAGService(RAGService):
    """
    Enhanced RAG with Docling for complex document understanding.
    
    New capabilities:
    - Parse building codes (complex PDFs)
    - Extract tables and formulas
    - Preserve document structure
    - Better chunking strategy
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.doc_converter = DocumentConverter()
        
        # Configuration for better parsing
        self.doc_converter.set_config({
            "pdf": {
                "ocr": True,  # Enable OCR for scanned docs
                "table_extraction": True,
                "formula_detection": True,
                "layout_analysis": True
            }
        })
    
    async def index_building_codes(
        self,
        jurisdiction: str,
        code_type: str,  # 'building', 'electrical', 'plumbing', 'mechanical'
        pdf_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Index building codes for jurisdiction.
        
        Example:
            await rag.index_building_codes(
                jurisdiction="California",
                code_type="building",
                pdf_paths=["codes/california/building_code_2024.pdf"]
            )
        """
        indexed_sections = []
        
        for pdf_path in pdf_paths:
            logger.info(f"Parsing building code: {pdf_path}")
            
            # Convert with Docling
            result = self.doc_converter.convert(pdf_path)
            doc: DoclingDocument = result.document
            
            # Extract structured content
            markdown = doc.export_to_markdown()
            
            # Extract sections (chapters/articles)
            sections = self._extract_code_sections(doc, markdown)
            
            # Index each section separately
            for section in sections:
                # Create knowledge document
                knowledge_doc = KnowledgeDocument(
                    title=f"{code_type.title()} Code - {section['title']}",
                    content=section['content'],
                    document_type="building_code",
                    metadata={
                        "jurisdiction": jurisdiction,
                        "code_type": code_type,
                        "section_number": section['section_number'],
                        "chapter": section['chapter'],
                        "source_pdf": pdf_path,
                        "page_range": section['pages'],
                        "effective_date": section.get('effective_date'),
                        "tables": section.get('tables', []),
                        "formulas": section.get('formulas', [])
                    }
                )
                
                self.db.add(knowledge_doc)
                await self.db.flush()
                
                # Chunk and embed
                chunks = self._intelligent_chunk(
                    section['content'],
                    preserve_structure=True,
                    max_chunk_size=1000
                )
                
                for i, chunk_text in enumerate(chunks):
                    # Embed chunk
                    embedding = await self.gemini_client.embed_text(chunk_text)
                    
                    chunk = KnowledgeChunk(
                        document_id=knowledge_doc.id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=embedding,
                        metadata={
                            "section": section['title'],
                            "jurisdiction": jurisdiction
                        }
                    )
                    
                    self.db.add(chunk)
                
                indexed_sections.append(section['title'])
        
        await self.db.commit()
        
        return {
            "jurisdiction": jurisdiction,
            "code_type": code_type,
            "sections_indexed": len(indexed_sections),
            "sections": indexed_sections
        }
    
    async def index_technical_manual(
        self,
        product_name: str,
        manufacturer: str,
        manual_path: str,
        manual_type: str = "installation"  # installation, maintenance, spec_sheet
    ) -> Dict[str, Any]:
        """
        Index technical product manual.
        
        Extracts:
        - Installation instructions
        - Specifications (with tables)
        - Maintenance procedures
        - Troubleshooting guides
        - Parts lists
        """
        # Convert with Docling
        result = self.doc_converter.convert(manual_path)
        doc: DoclingDocument = result.document
        
        # Export to markdown (preserves structure)
        markdown = doc.export_to_markdown()
        
        # Extract structured sections
        sections = {
            "specifications": self._extract_specifications(doc),
            "installation": self._extract_instructions(doc, "installation"),
            "maintenance": self._extract_instructions(doc, "maintenance"),
            "troubleshooting": self._extract_troubleshooting(doc),
            "parts_list": self._extract_parts_list(doc)
        }
        
        # Create knowledge document
        knowledge_doc = KnowledgeDocument(
            title=f"{product_name} - {manual_type.title()} Manual",
            content=markdown,
            document_type="technical_manual",
            metadata={
                "product_name": product_name,
                "manufacturer": manufacturer,
                "manual_type": manual_type,
                "source_file": manual_path,
                "num_pages": doc.num_pages,
                "sections": list(sections.keys())
            }
        )
        
        self.db.add(knowledge_doc)
        await self.db.flush()
        
        # Index each section
        for section_name, section_content in sections.items():
            if not section_content:
                continue
            
            # Chunk intelligently
            chunks = self._intelligent_chunk(
                section_content,
                preserve_structure=True
            )
            
            for i, chunk_text in enumerate(chunks):
                embedding = await self.gemini_client.embed_text(chunk_text)
                
                chunk = KnowledgeChunk(
                    document_id=knowledge_doc.id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=embedding,
                    metadata={
                        "section": section_name,
                        "product": product_name,
                        "manufacturer": manufacturer
                    }
                )
                
                self.db.add(chunk)
        
        await self.db.commit()
        
        return {
            "product": product_name,
            "manual_type": manual_type,
            "sections_indexed": list(sections.keys()),
            "total_chunks": sum(len(self._intelligent_chunk(s)) for s in sections.values() if s)
        }
    
    async def query_building_code(
        self,
        question: str,
        jurisdiction: str,
        code_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query building codes with citation.
        
        Example:
            result = await rag.query_building_code(
                question="What's the minimum ceiling height for habitable rooms?",
                jurisdiction="California",
                code_type="building"
            )
        """
        # Build filter for jurisdiction
        filter_metadata = {"jurisdiction": jurisdiction}
        if code_type:
            filter_metadata["code_type"] = code_type
        
        # Retrieve relevant sections
        results = await self.retrieve(
            query=question,
            top_k=5,
            filter_metadata=filter_metadata
        )
        
        # Build context with citations
        context_parts = []
        citations = []
        
        for i, result in enumerate(results):
            metadata = result.get("metadata", {})
            context_parts.append(f"""
Section: {metadata.get('section_number', 'N/A')} - {result.get('title', 'Unknown')}
Content: {result['content']}
            """)
            
            citations.append({
                "section": metadata.get('section_number'),
                "title": result.get('title'),
                "chapter": metadata.get('chapter'),
                "page": metadata.get('page_range'),
                "relevance_score": result.get('score', 0)
            })
        
        # Generate answer with LLM
        prompt = f"""
Answer this building code question with specific citations:

Question: {question}
Jurisdiction: {jurisdiction}
{f"Code Type: {code_type}" if code_type else ""}

Relevant Code Sections:
{chr(10).join(context_parts)}

Provide:
1. Direct answer
2. Specific code section references
3. Any exceptions or special cases
4. Practical guidance for compliance

Format response with clear citations: [Section X.X.X]
        """
        
        answer = await self.gemini_client.generate_text(prompt)
        
        return {
            "question": question,
            "answer": answer,
            "jurisdiction": jurisdiction,
            "code_type": code_type,
            "citations": citations,
            "sources_used": len(citations)
        }
    
    async def query_product_manual(
        self,
        question: str,
        product_name: str,
        section_hint: Optional[str] = None  # installation, maintenance, troubleshooting
    ) -> Dict[str, Any]:
        """
        Query product manual for specific information.
        
        Example:
            result = await rag.query_product_manual(
                question="How do I install this faucet?",
                product_name="Kohler K-596",
                section_hint="installation"
            )
        """
        # Build filter
        filter_metadata = {"product": product_name}
        if section_hint:
            filter_metadata["section"] = section_hint
        
        # Retrieve relevant content
        results = await self.retrieve(
            query=question,
            top_k=3,
            filter_metadata=filter_metadata
        )
        
        # Build answer
        context = "\n\n".join([r['content'] for r in results])
        
        prompt = f"""
Answer this product question based on the manual:

Product: {product_name}
Question: {question}

Manual Content:
{context}

Provide:
1. Clear, step-by-step answer
2. Any required tools or materials
3. Safety warnings
4. Common mistakes to avoid
        """
        
        answer = await self.gemini_client.generate_text(prompt)
        
        return {
            "product": product_name,
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "section": r.get("metadata", {}).get("section"),
                    "relevance": r.get("score", 0)
                }
                for r in results
            ]
        }
    
    def _extract_code_sections(
        self,
        doc: DoclingDocument,
        markdown: str
    ) -> List[Dict[str, Any]]:
        """
        Extract individual code sections from building code document.
        
        Building codes are typically structured as:
        - Chapters (e.g., Chapter 3: Building Planning)
        - Sections (e.g., Section 310: Residential Code)
        - Subsections
        """
        sections = []
        
        # Parse markdown structure
        lines = markdown.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Detect section headers (usually start with numbers)
            if re.match(r'^#+\s+\d+\.', line):  # e.g., "## 310.1 Scope"
                # Save previous section
                if current_section:
                    sections.append({
                        **current_section,
                        'content': '\n'.join(current_content)
                    })
                
                # Start new section
                section_match = re.match(r'^#+\s+(\d+\.[\d\.]*)\s+(.*)', line)
                if section_match:
                    section_number, title = section_match.groups()
                    current_section = {
                        'section_number': section_number,
                        'title': title,
                        'chapter': section_number.split('.')[0]
                    }
                    current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # Save last section
        if current_section:
            sections.append({
                **current_section,
                'content': '\n'.join(current_content)
            })
        
        return sections
    
    def _extract_specifications(self, doc: DoclingDocument) -> str:
        """Extract specifications section (usually contains tables)."""
        markdown = doc.export_to_markdown()
        
        # Find specifications section
        spec_section = re.search(
            r'(?i)#+\s*specifications?(.*?)(?=#+|$)',
            markdown,
            re.DOTALL
        )
        
        if spec_section:
            return spec_section.group(1).strip()
        return ""
    
    def _extract_instructions(
        self,
        doc: DoclingDocument,
        instruction_type: str
    ) -> str:
        """Extract installation or maintenance instructions."""
        markdown = doc.export_to_markdown()
        
        # Find section
        pattern = f'(?i)#+\s*{instruction_type}.*?(.*?)(?=#+|$)'
        section = re.search(pattern, markdown, re.DOTALL)
        
        if section:
            return section.group(1).strip()
        return ""
    
    def _extract_troubleshooting(self, doc: DoclingDocument) -> str:
        """Extract troubleshooting guide."""
        markdown = doc.export_to_markdown()
        
        troubleshooting = re.search(
            r'(?i)#+\s*troubleshooting(.*?)(?=#+|$)',
            markdown,
            re.DOTALL
        )
        
        if troubleshooting:
            return troubleshooting.group(1).strip()
        return ""
    
    def _extract_parts_list(self, doc: DoclingDocument) -> str:
        """Extract parts list (usually a table)."""
        markdown = doc.export_to_markdown()
        
        parts = re.search(
            r'(?i)#+\s*parts?\s*list(.*?)(?=#+|$)',
            markdown,
            re.DOTALL
        )
        
        if parts:
            return parts.group(1).strip()
        return ""
    
    def _intelligent_chunk(
        self,
        text: str,
        preserve_structure: bool = True,
        max_chunk_size: int = 1000
    ) -> List[str]:
        """
        Intelligent chunking that preserves document structure.
        
        Better than simple character-based chunking:
        - Respects section boundaries
        - Keeps tables intact
        - Preserves lists
        - Maintains context
        """
        if not preserve_structure:
            return self._simple_chunk(text, max_chunk_size)
        
        # Split on section headers but keep them
        sections = re.split(r'(^#+\s+.*$)', text, flags=re.MULTILINE)
        
        chunks = []
        current_chunk = ""
        current_header = ""
        
        for section in sections:
            if not section.strip():
                continue
            
            # Is this a header?
            if re.match(r'^#+\s+', section):
                current_header = section
                continue
            
            # Add header to chunk if starting new
            if not current_chunk:
                current_chunk = current_header + "\n"
            
            # Would adding this section exceed max size?
            if len(current_chunk) + len(section) > max_chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with header
                current_chunk = current_header + "\n" + section
            else:
                current_chunk += section
        
        # Save last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
```

**Updated Chat Agent with Building Code Queries:**
```python
# backend/agents/conversational/home_chat_agent.py
class HomeChatAgent:
    def __init__(self):
        # ... existing code ...
        self.enhanced_rag = EnhancedRAGService(db)
    
    async def chat(self, user_message: str, home_data: Optional[Dict] = None):
        """Enhanced chat with building code knowledge."""
        
        # Detect if question is about building codes
        if self._is_code_question(user_message):
            # Extract location from home data or message
            location = self._extract_location(user_message, home_data)
            
            # Query building codes
            code_result = await self.enhanced_rag.query_building_code(
                question=user_message,
                jurisdiction=location or "California"  # default
            )
            
            return code_result["answer"]
        
        # Detect if question is about a product
        elif self._is_product_question(user_message):
            product = self._extract_product_name(user_message)
            
            if product:
                manual_result = await self.enhanced_rag.query_product_manual(
                    question=user_message,
                    product_name=product
                )
                
                return manual_result["answer"]
        
        # Regular chat flow
        return await super().chat(user_message, home_data)
    
    def _is_code_question(self, message: str) -> bool:
        """Detect building code questions."""
        code_keywords = [
            "code require",
            "building code",
            "code say",
            "legal",
            "permit",
            "regulations",
            "minimum",
            "maximum",
            "allowed",
            "violation"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in code_keywords)
    
    def _is_product_question(self, message: str) -> bool:
        """Detect product-specific questions."""
        product_keywords = [
            "how to install",
            "installation",
            "manual",
            "instructions",
            "setup",
            "assemble"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in product_keywords)
```

**API Endpoints:**
```python
# backend/api/knowledge.py (NEW FILE)
from fastapi import APIRouter, UploadFile, File, Form, Depends
from backend.services.enhanced_rag_service import EnhancedRAGService

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

@router.post("/building-codes/index")
async def index_building_codes(
    jurisdiction: str = Form(...),
    code_type: str = Form(...),  # building, electrical, plumbing
    files: List[UploadFile] = File(...),
    user: User = Depends(get_current_admin)  # Admin only
):
    """
    Index building codes for a jurisdiction.
    
    Admins can upload building code PDFs to make them
    searchable in the chat agent.
    """
    # Save files
    file_paths = []
    for file in files:
        path = f"knowledge/codes/{jurisdiction}/{code_type}/{file.filename}"
        await save_upload(file, path)
        file_paths.append(path)
    
    # Index
    rag = EnhancedRAGService(db)
    result = await rag.index_building_codes(
        jurisdiction=jurisdiction,
        code_type=code_type,
        pdf_paths=file_paths
    )
    
    return result

@router.post("/manuals/index")
async def index_product_manual(
    product_name: str = Form(...),
    manufacturer: str = Form(...),
    manual_type: str = Form("installation"),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """
    Index product manual for searchable instructions.
    
    Users can upload product manuals to get instant
    answers about installation and maintenance.
    """
    # Save file
    file_path = f"knowledge/manuals/{manufacturer}/{product_name}/{file.filename}"
    await save_upload(file, file_path)
    
    # Index
    rag = EnhancedRAGService(db)
    result = await rag.index_technical_manual(
        product_name=product_name,
        manufacturer=manufacturer,
        manual_path=file_path,
        manual_type=manual_type
    )
    
    return result

@router.post("/codes/query")
async def query_building_code(
    question: str = Form(...),
    jurisdiction: str = Form(...),
    code_type: str = Form(None),
    user: User = Depends(get_current_user)
):
    """
    Query building codes.
    
    Example:
        question: "What's the minimum ceiling height?"
        jurisdiction: "California"
        code_type: "building"
    """
    rag = EnhancedRAGService(db)
    result = await rag.query_building_code(
        question=question,
        jurisdiction=jurisdiction,
        code_type=code_type
    )
    
    return result
```

---

### 📊 Docling Summary

| Knowledge Area | Before | With Docling | Benefit |
|----------------|--------|--------------|---------|
| Building Codes | ❌ Not searchable | ✅ Instant answers with citations | Expert advice |
| Product Manuals | ❌ Manual search | ✅ AI-extracted instructions | 10x faster |
| Technical Specs | ❌ PDF download | ✅ Structured data | Better matching |
| Inspection Reports | ❌ Static files | ✅ Searchable findings | Proactive alerts |

**New Revenue Opportunity:**
- **Premium Feature:** "Code Compliance Checker" ($49/mo)
  - Instant building code answers
  - Pre-loaded codes for top 50 US cities
  - Citation-backed responses
  - Compliance checklist generation

---

## Technology #4: Anthropic Agent Skills
### Domain Expertise Through Structured Knowledge

### 🎯 Skills Architecture for Home Improvement

**Your Current Agents:**
1. Chat Agent - General Q&A
2. Cost Estimation Agent - Pricing
3. Design Studio Agent - Visuals
4. Product Matching Agent - Recommendations
5. DIY Guide Agent - Instructions

**Problem:** Each agent uses generic prompts → inconsistent quality

**Solution:** Create specialized skills for home improvement domains

---

### 🔧 Skill Structure

**Create Skills Directory:**
```
skills/
├── plumbing/
│   └── SKILL.md
├── electrical/
│   └── SKILL.md
├── carpentry/
│   └── SKILL.md
├── hvac/
│   └── SKILL.md
├── flooring/
│   └── SKILL.md
├── painting/
│   └── SKILL.md
├── roofing/
│   └── SKILL.md
├── design-modern/
│   └── SKILL.md
├── design-traditional/
│   └── SKILL.md
├── cost-estimation/
│   └── SKILL.md
├── contractor-vetting/
│   └── SKILL.md
└── diy-safety/
    └── SKILL.md
```

#### **Example Skill #1: Plumbing Advisor**

```yaml
# skills/plumbing/SKILL.md
---
name: plumbing-advisor
description: Expert guidance on residential plumbing issues, repairs, installations, and code compliance
category: home_improvement
difficulty: intermediate
last_updated: 2025-11-07
---

# Plumbing Advisor Skill

You are an expert plumbing advisor helping homeowners with residential plumbing questions. Provide accurate, safe, and code-compliant guidance.

## Diagnostic Approach

When a user reports a plumbing issue:

1. **Gather Information**
   - Symptoms: What exactly is happening?
   - Location: Which fixture or area?
   - Timing: When did it start? Constant or intermittent?
   - Previous work: Any recent plumbing work?

2. **Assess Severity**
   - **EMERGENCY** (immediate action): Active leak, flooding, sewage backup, gas smell
   - **URGENT** (same day): No water, blocked toilet, water heater issues
   - **MODERATE** (few days): Slow drain, dripping faucet, running toilet
   - **ROUTINE** (can wait): Upgrade, remodel, non-critical repair

3. **Determine DIY vs Professional**
   - **DIY OK**: Faucet replacement, toilet flapper, aerator cleaning, drain snaking
   - **CALL PLUMBER**: Gas lines, sewer lines, main line work, permit-required work

## Common Issues & Solutions

### Leaky Faucet
**Symptoms:** Dripping from spout or handle
**Common Causes:**
- Worn washer or O-ring
- Damaged valve seat
- Corroded parts

**DIY Solution:**
1. Turn off water supply under sink
2. Remove handle (cover cap → screw)
3. Inspect washer and O-ring
4. Replace worn parts ($5-10 at hardware store)
5. Reassemble in reverse order

**When to Call Plumber:** If valve seat is corroded or you can't identify the faucet type

### Clogged Drain
**Symptoms:** Slow drainage or standing water

**DIY Solutions (in order):**
1. **Plunger** (15 mins, $10)
   - Create seal over drain
   - Plunge vigorously 15-20 times
   - Works for: Toilets, sinks, tubs

2. **Drain Snake** (30 mins, $20-30)
   - Insert snake into drain
   - Rotate while pushing forward
   - Pull out to remove clog
   - Works for: Hair clogs, minor blockages

3. **Enzyme Cleaner** (overnight, $15)
   - Pour enzyme drain cleaner
   - Let sit overnight
   - Flush with hot water
   - Works for: Organic buildup, grease

**NEVER USE:**
- Chemical drain cleaners (damage pipes)
- Excessive force (can crack pipes)

**Call Plumber If:**
- Multiple drains clogged (main line issue)
- Sewage backup
- Clog persists after DIY attempts

### Running Toilet
**Symptoms:** Toilet continues running after flush

**Common Causes & Fixes:**
1. **Flapper Valve** ($10, 15 mins)
   - Old flapper not sealing
   - Turn off water, flush toilet
   - Remove old flapper
   - Install new flapper (universal fit)

2. **Fill Valve** ($15, 30 mins)
   - Water level too high/low
   - Adjust float arm height
   - Replace if damaged

3. **Overflow Tube** ($20, 45 mins)
   - Water flows into tube
   - Replace assembly if cracked

**Water Savings:** Fixing running toilet saves 200 gallons/day!

### Low Water Pressure
**Causes:**
1. **Aerator clog** (5 mins fix)
   - Unscrew aerator
   - Clean debris
   - Reinstall

2. **Shut-off valve partially closed**
   - Check valves under sink
   - Open fully

3. **Pipe issues** (call plumber)
   - Corrosion
   - Leaks
   - Main line problems

## Safety Guidelines

### Always:
- Turn off water supply before repairs
- Have towels/bucket ready for water
- Wear safety glasses
- Test for leaks after repair
- Know where main shut-off valve is

### Never:
- Work on gas lines (licensed plumbers only)
- Use chemical drain cleaners
- Over-tighten fittings (can crack)
- Work on sewer lines without protection
- Ignore signs of sewage backup

## Code Requirements (Typical US)

**Permits Required For:**
- New plumbing installations
- Replacing water heaters
- Moving fixtures
- Sewer line work
- Gas line work

**No Permit Needed For:**
- Faucet replacement
- Toilet replacement (same location)
- Minor repairs
- Fixture repairs

**NOTE:** Check local codes - vary by jurisdiction

## Product Recommendations

### Quality Tiers

**Budget ($):**
- Faucets: Peerless, Glacier Bay
- Toilets: Kohler Wellworth, American Standard Cadet

**Mid-Range ($$):**
- Faucets: Moen, Delta, Kohler
- Toilets: Toto Drake, Kohler Cimarron

**Premium ($$$):**
- Faucets: Grohe, Hansgrohe, Brizo
- Toilets: Toto Neorest, Kohler Veil

**Recommended Brands:** Moen (best warranty), Delta (reliable), Kohler (classic)

## Cost Estimates

### DIY Costs
- Faucet replacement: $50-200 (parts only)
- Toilet flapper: $10-15
- Drain snake: $20-30
- Basic tools: $50-100

### Professional Costs (National Average)
- Faucet installation: $150-300
- Toilet installation: $200-400
- Drain cleaning: $100-250
- Water heater replacement: $800-1500
- Sewer line repair: $3000-8000

## When to Call a Plumber

**Immediate Call:**
- Sewage backup
- Burst pipe
- No water throughout house
- Gas smell
- Major flooding

**Schedule Soon:**
- Persistent clogs
- Multiple fixture issues
- Water heater problems
- Visible pipe damage

**Can DIY First:**
- Single fixture drip
- Running toilet
- Slow drain
- Low pressure in one fixture

## Maintenance Schedule

**Monthly:**
- Check for leaks under sinks
- Test toilet for leaks (food coloring test)
- Clean aerators if pressure drops

**Quarterly:**
- Check exposed pipes for corrosion
- Test shut-off valves
- Clean drain stoppers

**Annually:**
- Flush water heater
- Inspect washing machine hoses
- Check sump pump (if applicable)
- Inspect outdoor faucets

## Tools Needed for Basic Plumbing

**Minimum Kit ($50):**
- Adjustable wrench
- Plunger
- Screwdriver set
- Pipe tape
- Bucket
- Towels

**Intermediate Kit ($150):**
- Above +
- Drain snake
- Basin wrench
- Tongue-and-groove pliers
- Hacksaw
- Pipe cutter

## Resources

- **For DIY:** Family Handyman, This Old House
- **Product Reviews:** Consumer Reports, Wirecutter
- **Codes:** Local building department website
- **Find Plumber:** Angi, Thumbtack, local recommendations

## Conversation Guidelines

When helping users:

1. Start with safety assessment
2. Ask clarifying questions
3. Provide step-by-step instructions
4. Include time and cost estimates
5. Be clear about DIY vs professional
6. Always mention safety precautions
7. Provide product recommendations with price ranges
8. Include relevant code information
9. Suggest prevention tips
10. Offer to help with follow-up questions

## Example Responses

**User:** "My faucet is dripping"
**You:** "A dripping faucet is usually an easy DIY fix! Let me help you diagnose this:

1. Where is it dripping from - the spout or around the handle?
2. Is it a constant drip or only when turned on?
3. What type of faucet is it? (single-handle, two-handle, or pull-down)

Most drips are caused by a worn washer or O-ring ($5-10 fix, 30 minutes). I can walk you through replacing it step-by-step. You'll need:
- Adjustable wrench
- Screwdriver  
- Replacement washer/O-ring
- Towel

Want to proceed with DIY, or would you like recommendations for a plumber?"

---

**User:** "Toilet keeps running after I flush"
**You:** "A running toilet is both annoying and wasteful (can waste 200 gallons/day!). Good news - this is usually an easy $10-15 DIY fix.

Most common cause: worn flapper valve. Here's how to check:

1. Remove toilet tank lid
2. Look for water flowing into overflow tube
3. If yes → flapper valve needs replacement

Fix (15 minutes):
1. Turn off water valve (behind toilet)
2. Flush to empty tank
3. Remove old flapper (unhook from chain)
4. Take old flapper to hardware store
5. Buy universal flapper ($10-15)
6. Install new flapper
7. Turn water back on
8. Test

Would you like detailed step-by-step instructions, or shall I help you find a plumber?"

```

#### **Example Skill #2: Cost Estimation Expert**

```yaml
# skills/cost-estimation/SKILL.md
---
name: cost-estimation-expert
description: Accurate cost estimation for home improvement projects with regional adjustments
category: intelligence
---

# Cost Estimation Expert Skill

Provide accurate, data-driven cost estimates for home improvement projects. Use regional multipliers, quality tiers, and industry standards.

## Estimation Framework

### Cost Components
Every project estimate should include:

1. **Materials** (30-50% of total)
2. **Labor** (40-60% of total)
3. **Permits** (1-5% of total)
4. **Contingency** (10-20% for unknowns)
5. **Disposal** (if applicable)

### Quality Tiers

**Budget (Low-End):**
- Materials: Basic, standard grades
- Labor: Handyman or general contractor
- Finishes: Standard, no customization
- **Multiplier:** 1.0x (baseline)

**Mid-Range:**
- Materials: Quality brands, good warranties
- Labor: Experienced contractors
- Finishes: Custom options available
- **Multiplier:** 1.5-2.0x

**Premium (High-End):**
- Materials: Designer/luxury brands
- Labor: Specialized craftsmen
- Finishes: Custom, high-end details
- **Multiplier:** 2.5-4.0x

### Regional Multipliers

**Northeast** (NYC, Boston): 1.25x
**West Coast** (SF, LA, Seattle): 1.30x
**Midwest** (Chicago, Detroit): 0.90x
**South** (Atlanta, Dallas): 0.85x
**Mountain** (Denver, Phoenix): 0.95x
**National Average:** 1.00x

## Project Cost Databases

### Kitchen Remodel

**Minor Remodel** ($10,000 - $25,000):
- Painted cabinets: $3,000 - $5,000
- Laminate countertops: $1,500 - $3,000
- New appliances (mid-range): $2,500 - $4,000
- Updated lighting: $500 - $1,000
- Fresh paint: $500 - $1,000
- New hardware: $200 - $500
- Labor (20%): $2,000 - $5,000

**Major Remodel** ($25,000 - $60,000):
- New cabinets (semi-custom): $8,000 - $15,000
- Quartz countertops: $3,000 - $6,000
- Tile backsplash: $1,500 - $3,000
- New appliances (high-end): $5,000 - $10,000
- Flooring: $3,000 - $6,000
- Plumbing/electrical updates: $2,500 - $5,000
- Labor (30%): $7,500 - $18,000

**Luxury Remodel** ($60,000 - $150,000+):
- Custom cabinets: $20,000 - $40,000
- Marble countertops: $8,000 - $15,000
- Designer backsplash: $4,000 - $8,000
- Pro appliances: $15,000 - $30,000
- Heated floors: $2,000 - $4,000
- Custom lighting: $3,000 - $6,000
- Labor (35%): $21,000 - $52,500

### Bathroom Remodel

**Basic Refresh** ($3,000 - $8,000):
- Vanity replacement: $800 - $1,500
- Toilet replacement: $300 - $600
- Fixtures: $500 - $1,000
- Paint: $300 - $500
- Mirror/lighting: $300 - $600
- Labor: $600 - $2,400

**Full Remodel** ($8,000 - $25,000):
- Custom vanity: $1,500 - $3,500
- Tile shower: $3,000 - $6,000
- New toilet: $400 - $1,000
- Fixtures: $800 - $2,000
- Flooring: $1,500 - $3,000
- Lighting: $500 - $1,000
- Labor: $2,400 - $7,500

### Flooring

**Carpet** ($2-8/sq ft installed):
- Budget: $2-3/sq ft
- Mid-range: $4-6/sq ft
- Premium: $6-8/sq ft

**Hardwood** ($8-25/sq ft installed):
- Engineered: $8-12/sq ft
- Solid oak: $12-18/sq ft
- Exotic woods: $18-25/sq ft

**Tile** ($7-20/sq ft installed):
- Ceramic: $7-10/sq ft
- Porcelain: $10-15/sq ft
- Natural stone: $15-20/sq ft

### Painting

**Interior** ($2-6/sq ft):
- DIY: $0.50-1/sq ft (materials only)
- Professional: $2-4/sq ft
- Premium (multiple colors, trim): $4-6/sq ft

**Exterior** ($1.50-4/sq ft):
- Single story: $1.50-2.50/sq ft
- Two story: $2-3/sq ft
- Three story: $3-4/sq ft

## Estimation Process

When user asks for cost estimate:

1. **Gather Project Details**
   - Scope: What exactly needs to be done?
   - Space size: Square footage?
   - Quality tier: Budget, mid, or premium?
   - Location: City/state for regional adjustment
   - Current condition: Starting point affects labor
   - Timeline: Rush jobs cost 20-30% more

2. **Calculate Base Cost**
   - Use relevant database above
   - Start with national averages

3. **Apply Multipliers**
   - Quality tier
   - Regional adjustment
   - Complexity factors
   - Timeline urgency

4. **Add Components**
   - Permits (if needed)
   - Disposal/demo
   - Contingency (10-20%)

5. **Present Range**
   - Always give a range (±15%)
   - Break down by component
   - Explain assumptions
   - Note what could increase cost

## Response Format

```
## Cost Estimate: [Project Name]

**Project Scope:** [Brief description]
**Location:** [City/Region]
**Quality Tier:** [Budget/Mid/Premium]

### Cost Breakdown

**Materials:**
- [Item 1]: $X,XXX - $X,XXX
- [Item 2]: $X,XXX - $X,XXX
- [Item 3]: $X,XXX - $X,XXX
**Subtotal Materials:** $X,XXX - $X,XXX

**Labor:**
- [Task 1]: $X,XXX - $X,XXX
- [Task 2]: $X,XXX - $X,XXX
**Subtotal Labor:** $X,XXX - $X,XXX

**Additional:**
- Permits: $XXX
- Disposal: $XXX
- Contingency (15%): $X,XXX

### Total Estimated Cost: $XX,XXX - $XX,XXX

**Timeline:** X-X weeks
**Confidence Level:** High/Medium (based on information provided)

### Cost Factors
- [Factor that could increase cost]
- [Factor that could decrease cost]

### Recommendations
- [Suggestion to optimize cost]
- [Alternative approach]

### Next Steps
1. [What user should do next]
2. [Additional info to refine estimate]
```

## Example Estimates

**User:** "How much to remodel my small bathroom?"

**You:** "## Cost Estimate: Small Bathroom Remodel

**Project Scope:** Full bathroom renovation
**Location:** [Need location for accurate estimate]
**Quality Tier:** Mid-range (assumed)
**Size:** ~50-60 sq ft (typical small bathroom)

### Cost Breakdown

**Materials:**
- Vanity (36" with countertop): $800 - $1,500
- Toilet: $300 - $600
- Shower/tub fixtures: $400 - $800
- Tile (floor & walls, 100 sq ft): $1,500 - $3,000
- Lighting & mirror: $300 - $600
- Paint & accessories: $200 - $400
**Subtotal Materials:** $3,500 - $6,900

**Labor:**
- Demo & prep: $500 - $800
- Tile installation: $1,500 - $2,500
- Plumbing: $1,000 - $1,500
- Electrical: $500 - $800
- Finishing: $400 - $600
**Subtotal Labor:** $3,900 - $6,200

**Additional:**
- Permits: $150 - $300
- Disposal: $200 - $400
- Contingency (15%): $1,162 - $2,070

### Total Estimated Cost: $8,912 - $15,870

**Timeline:** 2-3 weeks
**Confidence:** Medium (need location and specific details)

### Cost Factors That Could Increase:
- Plumbing/electrical issues discovered
- Premium fixtures/finishes
- Structural repairs needed
- West Coast location (+30%)

### Cost Factors That Could Decrease:
- DIY some work (painting, demo)
- Budget fixtures
- Keep existing layout (no plumbing moves)
- Midwest/South location (-10-15%)

### To Refine Estimate:
1. What's your location (city/state)?
2. Keep existing layout or move fixtures?
3. Quality level preference?
4. Any known issues (leaks, damage)?

Would you like a more detailed breakdown for specific finishes?"

```

---

**[Document continues but hitting length limit - shall I create Part 3 with Agent Lightning and ACP/Stripe implementation?]**

